# tests/behavior/test_cloud_io.py

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# SSoT Alignment: Importing from your actual physical files
from src.io.dropbox_utils import TokenManager
from src.io.download_from_dropbox import CloudIngestor

@pytest.fixture
def mock_io_env(tmp_path):
    """Sets up a temporary local data vault and mock credentials."""
    data_dir = tmp_path / "data" / "testing-input-output"
    data_dir.mkdir(parents=True)
    
    log_file = tmp_path / "dropbox_download_log.txt"
    
    return {
        "data_dir": data_dir,
        "log_file": log_file,
        "app_key": "mock_key",
        "app_secret": "mock_secret",
        "refresh_token": "mock_refresh_token"
    }

def test_recursive_reconstruction(mock_io_env):
    """
    Scenario: Recursive Reconstruction
    Verifies that the Ingestor creates nested local paths from cloud artifacts.
    Compliance: Rule 1 (Precision Integrity).
    """
    # 1. Setup Mock TokenManager and Dropbox Client
    mock_tm = MagicMock(spec=TokenManager)
    mock_tm.refresh_access_token.return_value = "fake_access_token"
    
    with patch('dropbox.Dropbox') as mock_dbx_cls:
        mock_dbx = mock_dbx_cls.return_value
        
        # 2. Instantiate real Ingestor with injected dependencies
        ingestor = CloudIngestor(
            token_manager=mock_tm, 
            refresh_token=mock_io_env["refresh_token"], 
            log_path=mock_io_env["log_file"]
        )
        
        # 3. Mock the Dropbox file entries (Recursive Discovery)
        import dropbox
        mock_file = MagicMock(spec=dropbox.files.FileMetadata)
        mock_file.name = "data.h5"
        mock_file.path_lower = "/sim_v1/outputs/data.h5"
        
        mock_result = MagicMock()
        mock_result.entries = [mock_file]
        mock_result.has_more = False
        
        mock_dbx.files_list_folder.return_value = mock_result
        
        # Mock the actual binary download content
        mock_download_res = MagicMock()
        mock_download_res.content = b"binary_payload"
        mock_dbx.files_download.return_value = (None, mock_download_res)

        # 4. Execute Sync (using your actual method signature)
        ingestor.sync(
            source_folder="/sim_v1", 
            target_folder=mock_io_env["data_dir"], 
            allowed_ext=[".h5"]
        )
        
        # 5. Verification: Did it reconstruct the path 'sim_v1/outputs/data.h5'?
        # Note: In your code, relpath is calculated from source_folder
        target_file = Path(mock_io_env["data_dir"]) / "outputs" / "data.h5"
        assert target_file.exists()
        assert target_file.read_bytes() == b"binary_payload"

def test_token_expiry_recovery(mock_io_env):
    """
    Scenario: Token Refresh Handshake
    Verifies that CloudIngestor utilizes TokenManager to refresh sessions.
    Compliance: Rule 5 (Deterministic Init).
    """
    mock_tm = MagicMock(spec=TokenManager)
    mock_tm.refresh_access_token.return_value = "new_valid_token"
    
    with patch('dropbox.Dropbox') as mock_dbx_cls:
        # Trigger initialization
        CloudIngestor(
            token_manager=mock_tm, 
            refresh_token=mock_io_env["refresh_token"], 
            log_path=mock_io_env["log_file"]
        )
        
        # Logic: Refresh MUST have been called during __init__
        mock_tm.refresh_access_token.assert_called_with(mock_io_env["refresh_token"])
        # Logic: Dropbox client initialized with the new token
        mock_dbx_cls.assert_called_once_with("new_valid_token")

def test_extension_filtering(mock_io_env):
    """
    Verifies the Archivist only ingests relevant simulation artifacts (.h5, .zip).
    """
    mock_tm = MagicMock(spec=TokenManager)
    mock_tm.refresh_access_token.return_value = "token"
    
    with patch('dropbox.Dropbox') as mock_dbx_cls:
        mock_dbx = mock_dbx_cls.return_value
        ingestor = CloudIngestor(mock_tm, "ref", mock_io_env["log_file"])
        
        import dropbox
        # File 1: Allowed (.zip)
        f1 = MagicMock(spec=dropbox.files.FileMetadata)
        f1.name = "results.zip"
        f1.path_lower = "/results.zip"
        
        # File 2: Forbidden (.txt)
        f2 = MagicMock(spec=dropbox.files.FileMetadata)
        f2.name = "noise.txt"
        f2.path_lower = "/noise.txt"
        
        mock_result = MagicMock()
        mock_result.entries = [f1, f2]
        mock_result.has_more = False
        mock_dbx.files_list_folder.return_value = mock_result
        
        # Mock download response
        mock_res = MagicMock()
        mock_res.content = b"data"
        mock_dbx.files_download.return_value = (None, mock_res)

        # Execute
        ingestor.sync("/", mock_io_env["data_dir"], [".zip"])
        
        # Verification
        assert (Path(mock_io_env["data_dir"]) / "results.zip").exists()
        assert not (Path(mock_io_env["data_dir"]) / "noise.txt").exists()

def test_init_failure_hard_halt(mock_io_env):
    """
    Scenario: Auth Failure (Rule 4 Compliance)
    Verifies that the engine performs a Hard-Halt if the token cannot be refreshed.
    """
    mock_tm = MagicMock(spec=TokenManager)
    # Simulate a critical auth failure
    mock_tm.refresh_access_token.side_effect = RuntimeError("Invalid Grant")
    
    with pytest.raises(RuntimeError, match="Invalid Grant"):
        CloudIngestor(mock_tm, "bad_token", mock_io_env["log_file"])