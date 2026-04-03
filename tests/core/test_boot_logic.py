# tests/core/test_boot_logic.py

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Internal Core Imports
from src.core.bootloader import Bootloader
from src.core.state_engine import OrchestrationState
from src.core.constants import SystemPaths, OrchestrationStatus
from tests.helpers.state_engine_dummy import StateEngineDummy

@pytest.fixture
def boot_logic_env(tmp_path):
    """
    Sets up the physical nomadic node environment.
    Utilizes the Dummy Factory to ensure /schema and /config are correctly mapped.
    """
    # Create the base environment using our factory
    state, data_path = StateEngineDummy.create(tmp_path)
    
    config_dir = tmp_path / SystemPaths.CONFIG_DIR
    active_disk = config_dir / SystemPaths.ACTIVE_DISK
    ledger_path = config_dir / SystemPaths.LEDGER
    
    return {
        "root": tmp_path,
        "active_disk": active_disk,
        "ledger_path": ledger_path,
        "data_path": data_path,
        "config_dir": config_dir
    }

def test_bootloader_transformation_and_seeding_gate(boot_logic_env):
    """
    VERIFICATION: Transformation & Seeding Gate.
    Verifies Bootloader validates schemas AND seeds a fresh ledger with WAITING statuses.
    """
    # 1. Setup the 'Remote' Manifest Data
    mock_remote_manifest = {
        "manifest_id": "navier_stokes_v1_recon",
        "project_id": "TEST-PROJECT",
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
    with patch('src.core.bootloader.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_remote_manifest
        mock_get.return_value = mock_resp
        
        # --- PHASE 1: MOUNT ---
        state = Bootloader.mount(
            str(boot_logic_env["active_disk"]), 
            str(boot_logic_env["data_path"])
        )
        
        # --- PHASE 2: HYDRATE (Includes Seeding) ---
        Bootloader.hydrate(state)
        
        # 3. Final Verification
        assert isinstance(state, OrchestrationState)
        
        # Verify Local Identity
        assert state.project_id == "TEST-PROJECT"
        
        # Verify Ledger Seeding (Physical Truth Check)
        assert boot_logic_env["ledger_path"].exists()
        ledger_data = json.loads(boot_logic_env["ledger_path"].read_text())
        
        # Rule 4 Check: Step must exist and be explicitly WAITING
        step_entry = ledger_data["steps"]["navier_stokes_execution"]
        assert step_entry["status"] == OrchestrationStatus.WAITING.value
        assert step_entry["target_repo"] == "Dmitrii-Zavalin-Deployments/navier_stokes_solver"
        assert step_entry["last_triggered"] is None

def test_bootloader_network_failure_halt(boot_logic_env):
    """
    Scenario: Network Outage during Hydration (Rule 4).
    Verifies that a 404 triggers a Hard-Halt.
    """
    state = Bootloader.mount(
        str(boot_logic_env["active_disk"]), 
        str(boot_logic_env["data_path"])
    )
    
    with patch('src.core.bootloader.requests.get') as mock_get:
        mock_get.return_value.status_code = 404
        # Note: Hydrate now raises RuntimeError for any fetch/validation failure
        with pytest.raises(RuntimeError, match="Hydration failure"):
            Bootloader.hydrate(state)

def test_bootloader_schema_mismatch_halt(boot_logic_env):
    """
    Scenario: Schema Sovereignty Violation.
    Verifies that if the remote manifest is missing required keys (e.g., manifest_id), 
    the bootloader crashes rather than creating a corrupted state.
    """
    state = Bootloader.mount(
        str(boot_logic_env["active_disk"]), 
        str(boot_logic_env["data_path"])
    )
    
    # Poisoned data missing 'manifest_id' and 'project_id'
    poisoned_manifest = {
        "pipeline_steps": [] 
    }
    
    with patch('src.core.bootloader.requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = poisoned_manifest
        
        # Rule 4: Hard-Halt on Schema Breach
        with pytest.raises(RuntimeError, match="SCHEMA BREACH"):
            Bootloader.hydrate(state)