# tests/behavior/test_cloud_io.py

import pytest
from unittest.mock import patch
from src.io.cloud_ingestor import CloudIngestor
from src.io.token_manager import TokenManager

@pytest.fixture
def mock_io_env(tmp_path):
    """Sets up a temporary local data vault."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return {
        "data_dir": data_dir,
        "token_file": tmp_path / "refresh_token.txt"
    }

def test_recursive_reconstruction(mock_io_env):
    """
    Scenario: Recursive Reconstruction
    Verifies that the Ingestor creates nested local paths from cloud manifests.
    """
    ingestor = CloudIngestor(local_root=mock_io_env["data_dir"])
    
    # Mock cloud response: a file in a nested subdirectory
    mock_cloud_files = [
        {"path": "sim_v1/outputs/data.h5", "content": b"binary_payload"}
    ]
    
    with patch.object(ingestor, '_fetch_from_cloud', return_value=mock_cloud_files):
        ingestor.sync()
        
    # Verification: Did it create the directory 'sim_v1/outputs'?
    target_file = mock_io_env["data_dir"] / "sim_v1" / "outputs" / "data.h5"
    assert target_file.exists()
    assert target_file.read_bytes() == b"binary_payload"

def test_token_expiry_recovery(mock_io_env):
    """
    Scenario: Token Expiry Recovery (401 Handling)
    Verifies that a 401 response triggers a token refresh and retry.
    """
    tm = TokenManager(token_path=mock_io_env["token_file"])
    ingestor = CloudIngestor(local_root=mock_io_env["data_dir"], token_manager=tm)
    
    # Mock internal fetch to fail once with 401, then succeed
    with patch.object(ingestor, '_api_call') as mock_api:
        # First call: Raise 401. Second call: Return success.
        mock_api.side_effects = [
            Exception("401 Unauthorized"), 
            {"status": "success"}
        ]
        
        with patch.object(tm, 'refresh_access_token', return_value="new_valid_token") as mock_refresh:
            ingestor.sync_file("test.json")
            
            # Logic: Refresh MUST have been called
            mock_refresh.assert_called_once()
            # Logic: API should have been called twice (failure then success)
            assert mock_api.call_count == 2

def test_empty_sync_warning_logic(mock_io_env):
    """
    Scenario: Empty Sync Warning
    Verifies that the system identifies a 'Success with 0 files' as a potential failure.
    """
    ingestor = CloudIngestor(local_root=mock_io_env["data_dir"])
    
    # Cloud reports success but returns no files matching our extensions (.msh, .zip)
    mock_cloud_files = [] 
    
    with patch.object(ingestor, '_fetch_from_cloud', return_value=mock_cloud_files):
        # We expect the ingestor to raise a warning or return a specific exit code
        # to prevent the engine from falsely assuming the state is 'Saturated'.
        result = ingestor.sync()
        assert result.files_downloaded == 0
        assert result.status == "WARNING_EMPTY_SYNC"

def test_extension_filtering(mock_io_env):
    """
    Verifies the Archivist only ingests relevant simulation artifacts.
    """
    ingestor = CloudIngestor(local_root=mock_io_env["data_dir"])
    
    mock_cloud_files = [
        {"path": "results.zip", "content": b"zipped"},
        {"path": "unwanted_metadata.txt", "content": b"noise"}
    ]
    
    with patch.object(ingestor, '_fetch_from_cloud', return_value=mock_cloud_files):
        ingestor.sync()
        
    assert (mock_io_env["data_dir"] / "results.zip").exists()
    assert not (mock_io_env["data_dir"] / "unwanted_metadata.txt").exists()