# tests/io/test_download_from_dropbox.py

import pytest
import os
from unittest.mock import patch
from src.io.dropbox_utils import DropboxClient  # Assuming standard naming convention

# Rule 5: Operational Hygiene - Verifying Deterministic Sync Logic

class TestCloudIngestor:
    """
    Validation Suite for Infrastructure I/O.
    Ensures the 'Foundation' (Dropbox) can be reached deterministically.
    """

    @pytest.fixture
    def mock_env(self):
        """Rule 4: Zero-Default Policy - Testing against explicit environment keys."""
        with patch.dict(os.environ, {
            "DROPBOX_APP_KEY": "test_key",
            "DROPBOX_APP_SECRET": "test_secret",
            "DROPBOX_REFRESH_TOKEN": "test_refresh"
        }):
            yield

    def test_token_refresh_logic(self, mock_env):
        """
        Verifies that the ingestor handles token expiration without manual intervention.
        Compliance: Rule 5 (Nomadic Sustainability).
        """
        with patch('requests.post') as mock_post:
            # Simulate a successful OAuth2 refresh response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"access_token": "new_temp_token"}
            
            client = DropboxClient()
            token = client.refresh_access_token()
            
            assert token == "new_temp_token"
            mock_post.assert_called_once()
            print("\n✅ Token Refresh Logic: Deterministic")

    def test_pagination_continuity(self, mock_env):
        """
        Ensures 'list_folder' logic correctly follows cursors for large datasets.
        Rule 1: Isolation Mandate - Prevents partial artifact sync.
        """
        with patch('src.io.dropbox_utils.DropboxClient.call_api') as mock_api:
            # Mock a 2-page directory listing
            mock_api.side_effect = [
                {"entries": [{"name": "file1.json"}], "has_more": True, "cursor": "c1"},
                {"entries": [{"name": "file2.json"}], "has_more": False, "cursor": "c2"}
            ]
            
            client = DropboxClient()
            files = client.list_all_files("/test/path")
            
            assert len(files) == 2
            assert files[0]["name"] == "file1.json"
            assert files[1]["name"] == "file2.json"
            assert mock_api.call_count == 2
            print("\n✅ Pagination Logic: Deterministic")

    def test_hard_halt_on_auth_failure(self, mock_env):
        """
        Rule 4: Zero-Default Policy.
        The engine must crash if credentials are invalid, not proceed with empty data.
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 401 # Unauthorized
            
            client = DropboxClient()
            with pytest.raises(RuntimeError) as excinfo:
                client.refresh_access_token()
            
            assert "Access Denied" in str(excinfo.value)
            print("\n✅ Auth Failure: Hard-Halt Confirmed")