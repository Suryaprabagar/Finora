"""state_serializer.py — Finora state serialization with integrity metadata.

This module wraps the EXISTING ``backup_service.py`` export/restore
functionality and adds:

    - schema_version  (for forward-compatibility migration)
    - created_at      (ISO-8601 timestamp)
    - app_version     (from settings)
    - save_reason     (shutdown | autosave | manual | recovery)
    - checksum        (SHA-256 of the inner data JSON)
    - manifest metadata

The inner ``data`` dict produced by ``backup_service.export_user_data``
is unchanged — this wrapper adds an outer envelope and checksum.

Schema history
--------------
    v1  — initial schema (this implementation)

Migration
---------
    When loading state, the schema version is checked.  If it is older
    than the current version, ``migrate_state`` applies incremental
    migrations before restoring.  If it is newer than what this build
    supports, an error is raised so the user does not silently corrupt data.

IMPORTANT: Do NOT add business logic here. Serialization only.
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 1


class StateValidationError(Exception):
    """Raised when a loaded state fails validation."""


# ── Envelope construction ─────────────────────────────────────────────────────

def build_state_envelope(
    data: dict,
    *,
    save_reason: str = "manual",
    version: str = "",
    app_version: str = "1.0.0",
) -> dict:
    """Wrap *data* in the standard state envelope.

    Args:
        data:        The raw export dict from ``backup_service.export_user_data``.
        save_reason: One of ``controlled_shutdown``, ``autosave``, ``manual``, ``recovery``.
        version:     The version label (e.g. ``v006``).  Empty string for autosave.
        app_version: Application version string.

    Returns:
        A dict ready to be serialised to JSON and stored/uploaded.
    """
    data_json = json.dumps(data, ensure_ascii=False, sort_keys=True)
    checksum = hashlib.sha256(data_json.encode("utf-8")).hexdigest()

    return {
        "app": "Finora",
        "schema_version": CURRENT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "app_version": app_version,
        "save_reason": save_reason,
        "version": version,
        "checksum": checksum,
        "data": data,
    }


def build_manifest(
    state_bytes: bytes,
    *,
    version: str,
    previous_version: str = "",
    save_reason: str = "manual",
    status: str = "complete",
    app_version: str = "1.0.0",
) -> dict:
    """Build a manifest dict for a saved state.

    Args:
        state_bytes:      Raw bytes of the serialised state file.
        version:          Version label (e.g. ``v006``).
        previous_version: Label of the preceding version.
        save_reason:      Reason for saving.
        status:           ``complete`` or ``incomplete``.
        app_version:      Application version string.

    Returns:
        Manifest dict suitable for JSON serialisation.
    """
    checksum = hashlib.sha256(state_bytes).hexdigest()
    return {
        "version": version,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "app_version": app_version,
        "previous_version": previous_version,
        "status": status,
        "save_reason": save_reason,
        "files": {
            "state.json": {
                "size": len(state_bytes),
                "sha256": checksum,
            }
        },
    }


# ── Validation ────────────────────────────────────────────────────────────────

def validate_state(state: dict) -> None:
    """Validate the integrity and schema of a loaded state envelope.

    Args:
        state: The parsed state dict (loaded from state.json).

    Raises:
        StateValidationError: If validation fails for any reason.
    """
    # Presence checks
    for required in ("app", "schema_version", "checksum", "data"):
        if required not in state:
            raise StateValidationError(f"State missing required field: '{required}'")

    if state.get("app") != "Finora":
        raise StateValidationError(
            f"State 'app' field is not 'Finora': {state.get('app')}"
        )

    schema_ver = state.get("schema_version", 0)
    if schema_ver > CURRENT_SCHEMA_VERSION:
        raise StateValidationError(
            f"State schema version {schema_ver} is newer than this build supports "
            f"(max={CURRENT_SCHEMA_VERSION}). Please update Finora."
        )

    # Checksum verification
    data_json = json.dumps(state["data"], ensure_ascii=False, sort_keys=True)
    expected = hashlib.sha256(data_json.encode("utf-8")).hexdigest()
    if state["checksum"] != expected:
        raise StateValidationError(
            f"State checksum mismatch. Expected {expected}, got {state['checksum']}. "
            "The file may be corrupted."
        )

    logger.debug("State envelope validation passed (checksum OK).")


def validate_manifest(manifest: dict, state_bytes: bytes) -> None:
    """Validate a manifest dict against the actual state bytes.

    Args:
        manifest:    The parsed manifest dict (loaded from manifest.json).
        state_bytes: Raw bytes of state.json (downloaded from Drive).

    Raises:
        StateValidationError: If the manifest is incomplete or checksums do not match.
    """
    if manifest.get("status") != "complete":
        raise StateValidationError(
            f"Manifest status is not 'complete': {manifest.get('status')}"
        )

    schema_ver = manifest.get("schema_version", 0)
    if schema_ver > CURRENT_SCHEMA_VERSION:
        raise StateValidationError(
            f"Manifest schema version {schema_ver} is too new for this build."
        )

    file_meta = manifest.get("files", {}).get("state.json", {})
    expected_hash = file_meta.get("sha256", "")
    expected_size = file_meta.get("size", -1)

    if expected_size != len(state_bytes):
        raise StateValidationError(
            f"state.json size mismatch: manifest says {expected_size} bytes, "
            f"got {len(state_bytes)} bytes."
        )

    actual_hash = hashlib.sha256(state_bytes).hexdigest()
    if expected_hash and actual_hash != expected_hash:
        raise StateValidationError(
            f"state.json checksum mismatch: manifest sha256={expected_hash}, "
            f"actual sha256={actual_hash}."
        )

    logger.debug("Manifest validation passed.")


# ── Schema migration ──────────────────────────────────────────────────────────

def migrate_state(state: dict) -> dict:
    """Apply incremental schema migrations to bring *state* up to the current version.

    Each ``_migrate_v<N>_to_v<N+1>`` function handles one step.
    Migrations are applied in order until the state reaches
    ``CURRENT_SCHEMA_VERSION``.

    Args:
        state: Parsed state dict (possibly old schema version).

    Returns:
        State dict at the current schema version.
    """
    version = state.get("schema_version", 0)

    if version == CURRENT_SCHEMA_VERSION:
        return state

    if version > CURRENT_SCHEMA_VERSION:
        raise StateValidationError(
            f"Cannot migrate state from future schema version {version}."
        )

    # Apply migrations sequentially
    while version < CURRENT_SCHEMA_VERSION:
        migrator_name = f"_migrate_v{version}_to_v{version + 1}"
        migrator = globals().get(migrator_name)
        if migrator is None:
            raise StateValidationError(
                f"No migration function '{migrator_name}' found. "
                f"Cannot migrate state from schema v{version}."
            )
        logger.info(f"Migrating state from schema v{version} to v{version + 1}...")
        state = migrator(state)
        version = state.get("schema_version", version + 1)

    logger.info(f"State migrated to schema v{CURRENT_SCHEMA_VERSION}.")
    return state


# ── Migration functions (add new ones here as the schema evolves) ─────────────

# def _migrate_v0_to_v1(state: dict) -> dict:
#     """Example future migration: add a new field introduced in v1."""
#     state["schema_version"] = 1
#     state["data"].setdefault("new_field", [])
#     return state


# ── Serialisation helpers ─────────────────────────────────────────────────────

def serialize_to_bytes(envelope: dict) -> bytes:
    """Serialize an envelope dict to UTF-8 JSON bytes."""
    return json.dumps(envelope, ensure_ascii=False, indent=2).encode("utf-8")


def deserialize_from_bytes(raw: bytes) -> dict:
    """Deserialise raw UTF-8 JSON bytes into a dict.

    Raises:
        StateValidationError: On JSON parse error.
    """
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise StateValidationError(f"Failed to parse state JSON: {exc}") from exc
