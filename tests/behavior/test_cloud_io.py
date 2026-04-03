# tests/behavior/test_cloud_io.py

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import dropbox

# Internal Core Imports
from src.io.dropbox_utils import TokenManager
from src.io.download_from_dropbox import CloudIngestor
from src.core.constants import SystemPaths
from tests.helpers.state_engine_dummy import StateEngineDummy

@pytest.fixture
def cloud_env(tmp_path):
    """
    Sets up a physical nomadic data node and mock cloud credentials.
    Uses StateEngineDummy to ensure the data_path is architecturally correct.
    """
    state, data_path = StateEngineDummy.create(tmp_path)
    
    log_file = tmp_path / "dropbox_download_log.txt"
    
    return {
        "data_dir": data_path,
        "log_file": log_file,
        "refresh_token": "mock_refresh_token_123"
    }

def test_recursive_path_reconstruction(cloud_env):
    """
    Scenario: Recursive Reconstruction
    Verifies that the Ingestor reconstructs nested paths (e.g., /sim/out/data.h5) 
    locally inside the nomadic data vault.
    """
    # 1. Setup Mock TokenManager
    mock_tm = MagicMock(spec=TokenManager)
    mock_tm.refresh_access_token.return_value = "fake_access_token"
    
    with patch('dropbox.Dropbox') as mock_dbx_cls:
        mock_dbx = mock_dbx_cls.return_value
        
        # 2. Instantiate real Ingestor
        ingestor = CloudIngestor(
            token_manager=mock_tm, 
            refresh_token=cloud_env["refresh_token"], 
            log_path=cloud_env["log_file"]
        )
        
        # 3. Mock Dropbox Metadata (Simulating a nested file)
        mock_file = MagicMock(spec=dropbox.files.FileMetadata)
        mock_file.name = "simulation_results.h5"
        # The cloud path is deeper than the source root
        mock_file.path_lower = "/projects/oceans/outputs/simulation_results.h5"
        
        mock_result = MagicMock()
        mock_result.entries = [mock_file]
        mock_result.has_more = False
        mock_dbx.files_list_folder.return_value = mock_result
        
        # Mock the binary download stream
        mock_download_res = MagicMock()
        mock_download_res.content = b"FLUID_DYNAMICS_DATA_V1"
        mock_dbx.files_download.return_value = (None, mock_download_res)

        # 4. Execute Sync (Source: /projects/oceans)
        ingestor.sync(
            source_folder="/projects/oceans", 
            target_folder=cloud_env["data_dir"], 
            allowed_ext=[".h5"]
        )
        
        # 5. Verification: Path reconstruction check
        # Expected local: data/testing-input-output/outputs/simulation_results.h5
        target_file = Path(cloud_env["data_dir"]) / "outputs" / "simulation_results.h5"
        
        assert target_file.exists(), f"Failed to reconstruct path at {target_file}"
        assert target_file.read_bytes() == b"FLUID_DYNAMICS_DATA_V1"

def test_token_handshake_on_init(cloud_env):
    """
    Scenario: Deterministic Initialization (Rule 5)
    Verifies that CloudIngestor refreshes the token immediately upon instantiation.
    """
    mock_tm = MagicMock(spec=TokenManager)
    mock_tm.refresh_access_token.return_value = "fresh_session_token"
    
    with patch('dropbox.Dropbox') as mock_dbx_cls:
        CloudIngestor(
            token_manager=mock_tm, 
            refresh_token=cloud_env["refresh_token"], 
            log_path=cloud_env["log_file"]
        )
        
        # Logic: Must refresh using the provided secret
        mock_tm.refresh_access_token.assert_called_with(cloud_env["refresh_token"])
        # Logic: Dropbox client must be initialized with the resulting short-lived token
        mock_dbx_cls.assert_called_once_with("fresh_session_token")

def test_extension_security_gate(cloud_env):
    """
    Scenario: Extension Filtering
    Verifies the Ingestor ignores non-simulation files (Rule 1: Precision).
    """
    mock_tm = MagicMock(spec=TokenManager)
    mock_tm.refresh_access_token.return_value = "token"
    
    with patch('dropbox.Dropbox') as mock_dbx_cls:
        mock_dbx = mock_dbx_cls.return_value
        ingestor = CloudIngestor(mock_tm, "ref", cloud_env["log_file"])
        
        # File A: Valid Physics Artifact
        f1 = MagicMock(spec=dropbox.files.FileMetadata)
        f1.name = "mesh_v1.zip"
        f1.path_lower = "/mesh_v1.zip"
        
        # File B: Malicious or Irrelevant script
        f2 = MagicMock(spec=dropbox.files.FileMetadata)
        f2.name = "install.sh"
        f2.path_lower = "/install.sh"
        
        mock_result = MagicMock()
        mock_result.entries = [f1, f2]
        mock_result.has_more = False
        mock_dbx.files_list_folder.return_value = mock_result
        
        mock_res = MagicMock()
        mock_res.content = b"ZIP_DATA"
        mock_dbx.files_download.return_value = (None, mock_res)

        # Execute Sync allowing only .zip
        ingestor.sync("/", cloud_env["data_dir"], [".zip"])
        
        # Verification
        assert (Path(cloud_env["data_dir"]) / "mesh_v1.zip").exists()
        assert not (Path(cloud_env["data_dir"]) / "install.sh").exists()

def test_auth_failure_hard_halt(cloud_env):
    """
    Scenario: Zero-Default Policy (Rule 4)
    Verifies that a failed token refresh triggers a Hard-Halt.
    """
    mock_tm = MagicMock(spec=TokenManager)
    # Simulate a "Grant Expired" or "Network Down" scenario
    mock_tm.refresh_access_token.side_effect = RuntimeError("CLOUD_AUTH_DENIED")
    
    with pytest.raises(RuntimeError, match="CLOUD_AUTH_DENIED"):
        CloudIngestor(mock_tm, "expired_token", cloud_env["log_file"])