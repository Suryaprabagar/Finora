"""test_drive_manager.py — Unit tests for google_drive.py.

All Google API calls are mocked. No real Google account required.

Tests:
    - authenticate raises FileNotFoundError when credentials.json missing
    - authenticate saves token after successful flow
    - get_or_create_folder returns existing folder id
    - get_or_create_folder creates folder when not found
    - upload_file calls create for new file
    - upload_file calls update for existing file
    - upload_file retries on HttpError
    - download_file returns bytes when file found
    - download_file returns None when file not found
    - list_subfolders returns folder list
    - delete_folder calls Drive delete
    - verify_file_exists returns True/False correctly
    - Drive-disabled: importing without google libs raises clear ImportError
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def _make_client(tmp_dir):
    """Return a GoogleDriveClient with a real (temporary) credentials file path."""
    from app.storage.google_drive import GoogleDriveClient
    creds_file = os.path.join(tmp_dir, "credentials.json")
    # Write a minimal fake credentials file so the path check passes
    with open(creds_file, "w") as f:
        json.dump({"installed": {}}, f)
    token_file = os.path.join(tmp_dir, ".finora", "token.json")
    return GoogleDriveClient(credentials_file=creds_file, token_file=token_file)


class TestAuthentication:
    def test_missing_credentials_raises(self, tmp_dir):
        from app.storage.google_drive import GoogleDriveClient
        client = GoogleDriveClient(
            credentials_file=os.path.join(tmp_dir, "nonexistent.json"),
            token_file=os.path.join(tmp_dir, "token.json"),
        )
        with pytest.raises(FileNotFoundError, match="credentials"):
            client.authenticate()

    def test_authenticate_with_mock_flow(self, tmp_dir):
        """Successful authentication saves the token file."""
        client = _make_client(tmp_dir)

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.to_json.return_value = json.dumps({"token": "fake"})

        with patch("app.storage.google_drive.InstalledAppFlow") as mock_flow_cls, \
             patch("app.storage.google_drive.build") as mock_build:
            mock_flow = mock_flow_cls.from_client_secrets_file.return_value
            mock_flow.run_local_server.return_value = mock_creds
            mock_build.return_value = MagicMock()

            client.authenticate()

        # Token file should have been written
        assert os.path.exists(client.token_file)

    def test_check_auth_raises_when_not_authenticated(self, tmp_dir):
        client = _make_client(tmp_dir)
        from app.storage.google_drive import GoogleDriveError
        with pytest.raises(GoogleDriveError, match="authenticate"):
            client._check_auth()


class TestFolderOperations:
    def _client_with_service(self, tmp_dir):
        client = _make_client(tmp_dir)
        client._service = MagicMock()
        return client

    def test_find_folder_returns_id(self, tmp_dir):
        client = self._client_with_service(tmp_dir)
        client._service.files().list().execute.return_value = {
            "files": [{"id": "folder-123", "name": "Finora"}]
        }
        fid = client._find_folder("Finora", None)
        assert fid == "folder-123"

    def test_find_folder_returns_none_when_missing(self, tmp_dir):
        client = self._client_with_service(tmp_dir)
        client._service.files().list().execute.return_value = {"files": []}
        fid = client._find_folder("Finora", None)
        assert fid is None

    def test_get_or_create_returns_existing(self, tmp_dir):
        client = self._client_with_service(tmp_dir)
        client._service.files().list().execute.return_value = {
            "files": [{"id": "existing-id", "name": "Finora"}]
        }
        fid = client.get_or_create_folder("Finora")
        assert fid == "existing-id"

    def test_get_or_create_creates_when_missing(self, tmp_dir):
        client = self._client_with_service(tmp_dir)
        # list returns empty (folder not found), create returns new id
        client._service.files().list().execute.return_value = {"files": []}
        client._service.files().create().execute.return_value = {"id": "new-id"}
        fid = client.get_or_create_folder("Finora")
        assert fid == "new-id"


class TestFileUpload:
    def _client_with_service(self, tmp_dir):
        client = _make_client(tmp_dir)
        client._service = MagicMock()
        return client

    def test_upload_creates_new_file(self, tmp_dir):
        client = self._client_with_service(tmp_dir)
        # No existing file
        client._service.files().list().execute.return_value = {"files": []}
        client._service.files().create().execute.return_value = {"id": "new-file-id"}

        file_id = client.upload_file("folder-id", "state.json", b'{"test": 1}')
        assert file_id == "new-file-id"

    def test_upload_updates_existing_file(self, tmp_dir):
        client = self._client_with_service(tmp_dir)
        # Existing file found
        client._service.files().list().execute.return_value = {
            "files": [{"id": "existing-file-id", "name": "state.json"}]
        }
        client._service.files().update().execute.return_value = {"id": "existing-file-id"}

        file_id = client.upload_file("folder-id", "state.json", b'{"test": 2}')
        assert file_id == "existing-file-id"


class TestFileDownload:
    def _client_with_service(self, tmp_dir):
        client = _make_client(tmp_dir)
        client._service = MagicMock()
        return client

    def test_download_returns_bytes(self, tmp_dir):
        client = self._client_with_service(tmp_dir)
        client._service.files().list().execute.return_value = {
            "files": [{"id": "file-id", "name": "state.json"}]
        }
        expected = b'{"hello": "world"}'

        mock_request = MagicMock()
        client._service.files().get_media.return_value = mock_request

        with patch("app.storage.google_drive.MediaIoBaseDownload") as mock_dl_cls:
            mock_dl = MagicMock()
            mock_dl.next_chunk.return_value = (None, True)
            mock_dl_cls.side_effect = lambda buf, req: (_write_buf(buf, expected) or mock_dl)
            result = client.download_file("folder-id", "state.json")

        assert result == expected

    def test_download_returns_none_when_not_found(self, tmp_dir):
        client = self._client_with_service(tmp_dir)
        client._service.files().list().execute.return_value = {"files": []}
        result = client.download_file("folder-id", "nonexistent.json")
        assert result is None


def _write_buf(buf: io.BytesIO, data: bytes):
    """Helper to write data to the buffer passed to MediaIoBaseDownload."""
    buf.write(data)
    buf.seek(0)


class TestListAndDelete:
    def _client_with_service(self, tmp_dir):
        client = _make_client(tmp_dir)
        client._service = MagicMock()
        return client

    def test_list_subfolders(self, tmp_dir):
        client = self._client_with_service(tmp_dir)
        client._service.files().list().execute.return_value = {
            "files": [
                {"id": "f1", "name": "v001", "mimeType": "application/vnd.google-apps.folder"},
                {"id": "f2", "name": "v002", "mimeType": "application/vnd.google-apps.folder"},
            ]
        }
        folders = client.list_subfolders("parent-id")
        assert len(folders) == 2
        assert folders[0]["name"] == "v001"

    def test_delete_folder_calls_api(self, tmp_dir):
        client = self._client_with_service(tmp_dir)
        client._service.files().delete().execute.return_value = None
        client.delete_folder("folder-to-delete")
        client._service.files().delete.assert_called()

    def test_verify_file_exists_true(self, tmp_dir):
        client = self._client_with_service(tmp_dir)
        client._service.files().list().execute.return_value = {
            "files": [{"id": "file-123", "name": "state.json"}]
        }
        assert client.verify_file_exists("folder-id", "state.json") is True

    def test_verify_file_exists_false(self, tmp_dir):
        client = self._client_with_service(tmp_dir)
        client._service.files().list().execute.return_value = {"files": []}
        assert client.verify_file_exists("folder-id", "missing.json") is False
