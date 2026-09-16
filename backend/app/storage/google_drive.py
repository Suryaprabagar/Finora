"""google_drive.py — Low-level Google Drive API wrapper.

This module is the ONLY place in Finora that imports or calls
the Google Drive API. All other modules go through this wrapper.

Responsibilities:
    - OAuth2 authentication (browser-based, one-time)
    - Folder creation and lookup
    - File upload (with retry)
    - File download
    - File listing inside a folder
    - File deletion
    - Retry / error handling

NOT responsible for:
    - Finora business logic
    - SQLite
    - State serialization
    - Version management
"""
from __future__ import annotations

import io
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

# ── Optional import guard ─────────────────────────────────────────────────────
# The Google client libraries are only required when Drive is enabled.
# Importing them here with a clear error prevents confusing ImportErrors later.
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
    from googleapiclient.errors import HttpError
    _GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    _GOOGLE_LIBS_AVAILABLE = False

# Drive scope — read/write files created by this app only (narrowest scope).
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Retry configuration
_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 2.0


class GoogleDriveError(Exception):
    """Raised when a Google Drive operation fails after retries."""


class GoogleDriveClient:
    """Thin wrapper around the Google Drive v3 REST API.

    Usage::

        client = GoogleDriveClient(credentials_file="credentials.json",
                                   token_file=".finora/token.json")
        client.authenticate()
        folder_id = client.get_or_create_folder("Finora")
        client.upload_file(folder_id, "state.json", b"...")

    All public methods are synchronous (blocking). Callers that need
    async execution should run them inside ``asyncio.run_in_executor``.
    """

    def __init__(self, credentials_file: str, token_file: str) -> None:
        if not _GOOGLE_LIBS_AVAILABLE:
            raise ImportError(
                "Google Drive client libraries are not installed. "
                "Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )
        self.credentials_file = credentials_file
        self.token_file = token_file
        self._service = None  # set after authenticate()

    # ── Authentication ────────────────────────────────────────────────────────

    def authenticate(self) -> None:
        """Authenticate with Google Drive using OAuth2.

        On first run this opens a browser window for the user to grant
        permission.  The resulting token is saved to ``token_file`` and
        reused on subsequent runs.  When the token expires it is
        refreshed automatically without user interaction.

        Raises:
            FileNotFoundError: If ``credentials_file`` does not exist.
            GoogleDriveError: If authentication fails.
        """
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"Google Drive credentials file not found: {self.credentials_file}\n"
                "Please download credentials.json from Google Cloud Console and place it "
                "in the backend directory. See README.md for setup instructions."
            )

        creds: Optional[Credentials] = None

        # Load saved token if it exists
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as exc:
                logger.warning(f"Failed to load saved token, will re-authenticate: {exc}")
                creds = None

        # Refresh or obtain new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Google Drive token refreshed successfully.")
                except Exception as exc:
                    logger.warning(f"Token refresh failed, re-authenticating: {exc}")
                    creds = None

            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("Google Drive authentication completed.")
                except Exception as exc:
                    raise GoogleDriveError(
                        f"Google Drive authentication failed: {exc}"
                    ) from exc

            # Save the token for next run
            os.makedirs(os.path.dirname(self.token_file) or ".", exist_ok=True)
            with open(self.token_file, "w") as fh:
                fh.write(creds.to_json())
            logger.info(f"Google Drive token saved to {self.token_file}")

        self._service = build("drive", "v3", credentials=creds)
        logger.info("Google Drive client initialized.")

    def _check_auth(self) -> None:
        """Raise if ``authenticate()`` has not been called."""
        if self._service is None:
            raise GoogleDriveError(
                "GoogleDriveClient.authenticate() must be called before any Drive operations."
            )

    # ── Folder operations ─────────────────────────────────────────────────────

    def get_or_create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Return the folder ID for *name*, creating it if necessary.

        Args:
            name:      Folder name to look up or create.
            parent_id: Parent folder ID.  If None, creates at root.

        Returns:
            Google Drive folder ID string.
        """
        self._check_auth()
        folder_id = self._find_folder(name, parent_id)
        if folder_id:
            return folder_id
        return self._create_folder(name, parent_id)

    def _find_folder(self, name: str, parent_id: Optional[str]) -> Optional[str]:
        """Return the folder ID if the folder exists, else None."""
        query = (
            f"name = '{name}' "
            f"and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )
        if parent_id:
            query += f" and '{parent_id}' in parents"
        try:
            response = (
                self._service.files()
                .list(q=query, spaces="drive", fields="files(id, name)")
                .execute()
            )
            files = response.get("files", [])
            if files:
                return files[0]["id"]
        except HttpError as exc:
            logger.error(f"Drive API error finding folder '{name}': {exc}")
        return None

    def _create_folder(self, name: str, parent_id: Optional[str]) -> str:
        """Create a folder and return its ID."""
        metadata: dict = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [parent_id]
        try:
            folder = (
                self._service.files().create(body=metadata, fields="id").execute()
            )
            folder_id = folder["id"]
            logger.info(f"Created Drive folder '{name}' (id={folder_id})")
            return folder_id
        except HttpError as exc:
            raise GoogleDriveError(f"Failed to create Drive folder '{name}': {exc}") from exc

    # ── File upload ───────────────────────────────────────────────────────────

    def upload_file(
        self,
        folder_id: str,
        filename: str,
        content: bytes,
        mime_type: str = "application/json",
    ) -> str:
        """Upload *content* as *filename* in *folder_id*, replacing any existing file.

        Args:
            folder_id: Drive folder ID to upload into.
            filename:  Name of the file on Drive.
            content:   Raw bytes to upload.
            mime_type: MIME type for the upload.

        Returns:
            Drive file ID of the uploaded file.

        Raises:
            GoogleDriveError: If the upload fails after retries.
        """
        self._check_auth()
        existing_id = self._find_file(filename, folder_id)

        media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=False)

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                if existing_id:
                    # Update existing file
                    result = (
                        self._service.files()
                        .update(fileId=existing_id, media_body=media, fields="id")
                        .execute()
                    )
                else:
                    # Create new file
                    metadata = {"name": filename, "parents": [folder_id]}
                    result = (
                        self._service.files()
                        .create(body=metadata, media_body=media, fields="id")
                        .execute()
                    )
                file_id = result["id"]
                logger.debug(f"Uploaded '{filename}' to Drive (id={file_id}, attempt={attempt})")
                return file_id
            except HttpError as exc:
                logger.warning(f"Upload attempt {attempt}/{_MAX_RETRIES} failed for '{filename}': {exc}")
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY_SECONDS * attempt)
                else:
                    raise GoogleDriveError(
                        f"Failed to upload '{filename}' after {_MAX_RETRIES} attempts: {exc}"
                    ) from exc
        # Should never reach here
        raise GoogleDriveError(f"Upload failed for '{filename}'")

    # ── File download ─────────────────────────────────────────────────────────

    def download_file(self, folder_id: str, filename: str) -> Optional[bytes]:
        """Download *filename* from *folder_id*.

        Returns:
            Raw bytes of the file content, or None if the file does not exist.

        Raises:
            GoogleDriveError: If the download fails after retries.
        """
        self._check_auth()
        file_id = self._find_file(filename, folder_id)
        if not file_id:
            return None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                request = self._service.files().get_media(fileId=file_id)
                buf = io.BytesIO()
                downloader = MediaIoBaseDownload(buf, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                logger.debug(f"Downloaded '{filename}' from Drive (attempt={attempt})")
                return buf.getvalue()
            except HttpError as exc:
                logger.warning(f"Download attempt {attempt}/{_MAX_RETRIES} failed for '{filename}': {exc}")
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY_SECONDS * attempt)
                else:
                    raise GoogleDriveError(
                        f"Failed to download '{filename}' after {_MAX_RETRIES} attempts: {exc}"
                    ) from exc
        raise GoogleDriveError(f"Download failed for '{filename}'")

    # ── File listing ──────────────────────────────────────────────────────────

    def list_files(self, folder_id: str) -> list[dict]:
        """List all non-trashed files in *folder_id*.

        Returns:
            List of dicts with keys ``id``, ``name``.
        """
        self._check_auth()
        query = f"'{folder_id}' in parents and trashed = false"
        try:
            response = (
                self._service.files()
                .list(q=query, spaces="drive", fields="files(id, name, mimeType)")
                .execute()
            )
            return response.get("files", [])
        except HttpError as exc:
            raise GoogleDriveError(f"Failed to list Drive folder contents: {exc}") from exc

    def list_subfolders(self, parent_id: str) -> list[dict]:
        """List all non-trashed subfolders inside *parent_id*.

        Returns:
            List of dicts with keys ``id``, ``name``.
        """
        self._check_auth()
        query = (
            f"'{parent_id}' in parents "
            f"and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )
        try:
            response = (
                self._service.files()
                .list(q=query, spaces="drive", fields="files(id, name)")
                .execute()
            )
            return response.get("files", [])
        except HttpError as exc:
            raise GoogleDriveError(f"Failed to list subfolders: {exc}") from exc

    # ── File deletion ─────────────────────────────────────────────────────────

    def delete_folder(self, folder_id: str) -> None:
        """Permanently delete a folder and its contents from Drive.

        Args:
            folder_id: Drive folder ID to delete.
        """
        self._check_auth()
        try:
            self._service.files().delete(fileId=folder_id).execute()
            logger.info(f"Deleted Drive folder id={folder_id}")
        except HttpError as exc:
            raise GoogleDriveError(f"Failed to delete Drive folder id={folder_id}: {exc}") from exc

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _find_file(self, filename: str, folder_id: str) -> Optional[str]:
        """Return the file ID for *filename* in *folder_id*, or None."""
        query = (
            f"name = '{filename}' "
            f"and '{folder_id}' in parents "
            f"and trashed = false"
        )
        try:
            response = (
                self._service.files()
                .list(q=query, spaces="drive", fields="files(id, name)")
                .execute()
            )
            files = response.get("files", [])
            return files[0]["id"] if files else None
        except HttpError as exc:
            logger.error(f"Drive API error finding file '{filename}': {exc}")
            return None

    def verify_file_exists(self, folder_id: str, filename: str) -> bool:
        """Return True if *filename* exists in *folder_id*."""
        return self._find_file(filename, folder_id) is not None
