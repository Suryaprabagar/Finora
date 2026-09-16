"""test_state_serializer.py — Unit tests for state_serializer.py.

Tests:
    - build_state_envelope produces valid envelope
    - checksum is correct
    - validate_state passes on valid envelope
    - validate_state raises on wrong app name
    - validate_state raises on checksum mismatch
    - validate_state raises on future schema version
    - build_manifest produces correct size and sha256
    - validate_manifest passes on valid manifest/bytes
    - validate_manifest raises on incomplete status
    - validate_manifest raises on size mismatch
    - validate_manifest raises on sha256 mismatch
    - migrate_state is a no-op when schema version is current
    - migrate_state raises on future schema version
    - serialize_to_bytes / deserialize_from_bytes round-trip
    - deserialize_from_bytes raises on invalid JSON
"""
from __future__ import annotations

import hashlib
import json
import sys
import os

import pytest

# Make sure backend/ is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.storage.state_serializer import (
    CURRENT_SCHEMA_VERSION,
    StateValidationError,
    build_manifest,
    build_state_envelope,
    deserialize_from_bytes,
    migrate_state,
    serialize_to_bytes,
    validate_manifest,
    validate_state,
)


# ── build_state_envelope ──────────────────────────────────────────────────────

class TestBuildStateEnvelope:
    def test_produces_required_fields(self, sample_data):
        env = build_state_envelope(sample_data, save_reason="test", version="v001")
        for field in ("app", "schema_version", "created_at", "app_version",
                      "save_reason", "version", "checksum", "data"):
            assert field in env, f"Missing field: {field}"

    def test_app_is_finora(self, sample_data):
        env = build_state_envelope(sample_data)
        assert env["app"] == "Finora"

    def test_schema_version_is_current(self, sample_data):
        env = build_state_envelope(sample_data)
        assert env["schema_version"] == CURRENT_SCHEMA_VERSION

    def test_checksum_is_correct(self, sample_data):
        env = build_state_envelope(sample_data)
        data_json = json.dumps(sample_data, ensure_ascii=False, sort_keys=True)
        expected = hashlib.sha256(data_json.encode()).hexdigest()
        assert env["checksum"] == expected

    def test_data_preserved(self, sample_data):
        env = build_state_envelope(sample_data)
        assert env["data"] == sample_data

    def test_save_reason_stored(self, sample_data):
        env = build_state_envelope(sample_data, save_reason="controlled_shutdown")
        assert env["save_reason"] == "controlled_shutdown"


# ── validate_state ────────────────────────────────────────────────────────────

class TestValidateState:
    def test_valid_envelope_passes(self, sample_envelope):
        validate_state(sample_envelope)  # should not raise

    def test_missing_field_raises(self, sample_envelope):
        del sample_envelope["checksum"]
        with pytest.raises(StateValidationError, match="checksum"):
            validate_state(sample_envelope)

    def test_wrong_app_raises(self, sample_envelope):
        sample_envelope["app"] = "NotFinora"
        with pytest.raises(StateValidationError, match="app"):
            validate_state(sample_envelope)

    def test_checksum_mismatch_raises(self, sample_envelope):
        sample_envelope["checksum"] = "deadbeef" * 8
        with pytest.raises(StateValidationError, match="checksum"):
            validate_state(sample_envelope)

    def test_future_schema_raises(self, sample_envelope):
        sample_envelope["schema_version"] = CURRENT_SCHEMA_VERSION + 99
        with pytest.raises(StateValidationError, match="schema version"):
            validate_state(sample_envelope)

    def test_data_mutation_invalidates_checksum(self, sample_envelope):
        sample_envelope["data"]["injected"] = "evil"
        with pytest.raises(StateValidationError, match="checksum"):
            validate_state(sample_envelope)


# ── build_manifest / validate_manifest ───────────────────────────────────────

class TestManifest:
    def test_manifest_contains_sha256(self, sample_envelope_bytes):
        m = build_manifest(sample_envelope_bytes, version="v001")
        assert "sha256" in m["files"]["state.json"]

    def test_manifest_contains_size(self, sample_envelope_bytes):
        m = build_manifest(sample_envelope_bytes, version="v001")
        assert m["files"]["state.json"]["size"] == len(sample_envelope_bytes)

    def test_valid_manifest_passes(self, sample_envelope_bytes, sample_manifest):
        validate_manifest(sample_manifest, sample_envelope_bytes)  # no raise

    def test_incomplete_status_raises(self, sample_envelope_bytes, sample_manifest):
        sample_manifest["status"] = "incomplete"
        with pytest.raises(StateValidationError, match="status"):
            validate_manifest(sample_manifest, sample_envelope_bytes)

    def test_size_mismatch_raises(self, sample_envelope_bytes, sample_manifest):
        sample_manifest["files"]["state.json"]["size"] = 0
        with pytest.raises(StateValidationError, match="size"):
            validate_manifest(sample_manifest, sample_envelope_bytes)

    def test_sha256_mismatch_raises(self, sample_envelope_bytes, sample_manifest):
        sample_manifest["files"]["state.json"]["sha256"] = "bad" + "0" * 61
        with pytest.raises(StateValidationError, match="checksum"):
            validate_manifest(sample_manifest, sample_envelope_bytes)

    def test_future_schema_in_manifest_raises(self, sample_envelope_bytes, sample_manifest):
        sample_manifest["schema_version"] = CURRENT_SCHEMA_VERSION + 5
        with pytest.raises(StateValidationError, match="schema version"):
            validate_manifest(sample_manifest, sample_envelope_bytes)


# ── migrate_state ─────────────────────────────────────────────────────────────

class TestMigrateState:
    def test_current_version_is_noop(self, sample_envelope):
        result = migrate_state(sample_envelope)
        assert result is sample_envelope

    def test_future_version_raises(self, sample_envelope):
        sample_envelope["schema_version"] = CURRENT_SCHEMA_VERSION + 1
        with pytest.raises(StateValidationError, match="future schema"):
            migrate_state(sample_envelope)


# ── Serialization round-trip ──────────────────────────────────────────────────

class TestSerializationRoundTrip:
    def test_roundtrip(self, sample_envelope):
        raw = serialize_to_bytes(sample_envelope)
        restored = deserialize_from_bytes(raw)
        assert restored == sample_envelope

    def test_invalid_json_raises(self):
        with pytest.raises(StateValidationError, match="JSON"):
            deserialize_from_bytes(b"not-json{{{")
