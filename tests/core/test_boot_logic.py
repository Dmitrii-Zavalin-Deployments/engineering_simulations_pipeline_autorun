# tests/core/test_boot_logic.py

import pytest
from unittest.mock import patch, MagicMock

# Internal Core Imports
from src.core.bootloader import Bootloader
from src.core.state_engine import OrchestrationState
from src.core.constants import SystemPaths
from tests.helpers.state_engine_dummy import StateEngineDummy

@pytest.fixture
def boot_logic_env(tmp_path):
    """
    Sets up the physical wake-up environment.
    Utilizes the Dummy Factory to ensure the core_schema.json is physically present.
    """
    # Create the base environment using our factory
    state, data_path = StateEngineDummy.create(tmp_path)
    
    config_dir = tmp_path / SystemPaths.CONFIG_DIR
    active_disk = config_dir / SystemPaths.ACTIVE_DISK
    
    return {
        "root": tmp_path,
        "active_disk": active_disk,
        "data_path": data_path,
        "config_dir": config_dir
    }

def test_bootloader_transformation_gate(boot_logic_env):
    """
    VERIFICATION: Transformation Gate.
    Verifies Bootloader can merge local 'active_disk' config with remote 'manifest' JSON
    into a functional, validated OrchestrationState object.
    """
    # 1. Setup the 'Remote' Manifest Data
    # This simulates the JSON your engine fetches from GitHub/S3
    mock_remote_manifest = {
        "manifest_id": "navier_stokes_v1_recon",
        "project_id": "TEST-PROJECT",  # Must match the project_id in StateEngineDummy
        "pipeline_steps": [
            {
                "name": "navier_stokes_execution",
                "target_repo": "Dmitrii-Zavalin-Deployments/navier_stokes_solver",
                "requires": ["fluid_input.json"],
                "produces": ["fluid_output.zip"],
                "timeout_hours": 6
            }
        ]
    }

    # 2. Execute Bootloader Sequence with Mocked Network
    # We patch 'requests' specifically inside the bootloader module
    with patch('src.core.bootloader.requests.get') as mock_get:
        # Configure Mock Response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_remote_manifest
        mock_get.return_value = mock_resp
        
        # --- PHASE 1: MOUNT ---
        # Loads project_id and manifest_url from local active_disk.json
        state = Bootloader.mount(
            str(boot_logic_env["active_disk"]), 
            str(boot_logic_env["data_path"])
        )
        
        # --- PHASE 2: HYDRATE ---
        # Fetches remote JSON, validates against local schema, and hydrates attributes
        Bootloader.hydrate(state)
        
        # 3. Final Verification
        assert isinstance(state, OrchestrationState)
        
        # Verify Local Identity (from active_disk.json)
        assert state.project_id == "TEST-PROJECT"
        
        # Verify Remote Identity (from the hydrated manifest)
        assert state.manifest_data["manifest_id"] == "navier_stokes_v1_recon"
        
        # Verify Pipeline Integrity
        step = state.manifest_data["pipeline_steps"][0]
        assert step["name"] == "navier_stokes_execution"
        assert "navier_stokes_solver" in step["target_repo"]

def test_bootloader_network_failure_halt(boot_logic_env):
    """
    Scenario: Network Outage during Hydration (Rule 4).
    Verifies that a 404 or connection error triggers a Hard-Halt.
    """
    state = Bootloader.mount(
        str(boot_logic_env["active_disk"]), 
        str(boot_logic_env["data_path"])
    )
    
    with patch('src.core.bootloader.requests.get') as mock_get:
        mock_get.return_value.status_code = 404
        
        with pytest.raises(RuntimeError, match="Failed to fetch manifest"):
            Bootloader.hydrate(state)

def test_bootloader_schema_mismatch_halt(boot_logic_env):
    """
    Scenario: Schema Sovereignty Violation.
    Verifies that if the remote manifest returns invalid fields, 
    the bootloader crashes rather than creating a corrupted state.
    """
    state = Bootloader.mount(
        str(boot_logic_env["active_disk"]), 
        str(boot_logic_env["data_path"])
    )
    
    # Poisoned data missing 'manifest_id'
    poisoned_manifest = {
        "pipeline_steps": [] 
    }
    
    with patch('src.core.bootloader.requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = poisoned_manifest
        
        with pytest.raises(RuntimeError, match="Manifest is corrupt"):
            Bootloader.hydrate(state)