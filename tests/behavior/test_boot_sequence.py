# tests/behavior/test_boot_sequence.py

import pytest
import json
import time
import os
from unittest.mock import patch, MagicMock
from src.core.bootloader import Bootloader
from src.core.state_engine import OrchestrationState
from src.core.constants import SystemPaths
from tests.helpers.state_engine_dummy import StateEngineDummy

@pytest.fixture
def boot_env(tmp_path):
    """
    Creates the physical environment for boot testing.
    Uses the dummy factory to ensure schema and paths are correct.
    """
    state, data_path = StateEngineDummy.create(tmp_path)
    
    config_dir = tmp_path / SystemPaths.CONFIG_DIR
    active_disk = config_dir / SystemPaths.ACTIVE_DISK
    dormant_flag = config_dir / SystemPaths.DORMANT_FLAG
    ledger_path = config_dir / SystemPaths.LEDGER
    
    return {
        "root": tmp_path,
        "config_dir": config_dir,
        "active_disk": active_disk,
        "dormant_flag": dormant_flag,
        "ledger_path": ledger_path,
        "data_path": data_path
    }

def test_clean_wakeup_mounting(boot_env):
    """
    Scenario: Clean Wake-Up
    Verifies that Bootloader.mount returns a valid OrchestrationState.
    """
    state = Bootloader.mount(
        str(boot_env["active_disk"]), 
        str(boot_env["data_path"]),
        str(boot_env["ledger_path"])
    )
    
    assert isinstance(state, OrchestrationState)
    assert state.project_id == "TEST-PROJECT"
    assert str(state.data_path) == str(boot_env["data_path"])

def test_auto_wake_logic(boot_env):
    """
    Scenario: Auto-Wake Trigger
    Verifies that a newer active_disk.json flips DORMANT to ACTIVE.
    """
    boot_env["dormant_flag"].write_text("STATUS: DORMANT", encoding="utf-8")
    
    new_time = time.time() + 10
    os.utime(boot_env["active_disk"], (new_time, new_time))
    
    Bootloader.mount(
        str(boot_env["active_disk"]), 
        str(boot_env["data_path"]),
        str(boot_env["ledger_path"])
    )
    
    content = boot_env["dormant_flag"].read_text(encoding="utf-8")
    assert "ACTIVE" in content.upper()

def test_poisoned_manifest_schema_gate(boot_env):
    """
    Scenario: Poisoned Manifest (Schema Enforcement)
    """
    state = Bootloader.mount(
        str(boot_env["active_disk"]), 
        str(boot_env["data_path"]),
        str(boot_env["ledger_path"])
    )
    
    poisoned_data = {
        "manifest_id": "FAIL-001",
        "project_id": "POISON-PROJECT"
    }
    
    with pytest.raises(RuntimeError) as excinfo:
        state.hydrate_manifest(poisoned_data)
    
    assert "Hard-Halt" in str(excinfo.value)

def test_missing_config_halt(boot_env):
    """
    Scenario: Missing Foundation
    """
    missing_path = boot_env["config_dir"] / "non_existent.json"
    
    with pytest.raises(RuntimeError) as excinfo:
        Bootloader.mount(
            str(missing_path), 
            str(boot_env["data_path"]),
            str(boot_env["ledger_path"])
        )
    
    assert "Mounting Failed" in str(excinfo.value)

def test_ledger_wipe_on_project_shift(boot_env):
    """
    Scenario: Project ID Mismatch
    Verifies that if the remote manifest ID differs from the local ledger,
    the ledger is wiped to prevent data pollution.
    """
    ledger_path = boot_env["ledger_path"]
    stale_ledger = {
        "metadata": {"project_id": "OLD-PROJECT", "manifest_id": "OLD-MID"},
        "steps": {"old_step": {"status": "COMPLETED"}}
    }
    ledger_path.write_text(json.dumps(stale_ledger), encoding="utf-8")
    
    state = Bootloader.mount(
        str(boot_env["active_disk"]), 
        str(boot_env["data_path"]),
        str(ledger_path)
    )
    
    # REPLACED requests_mock with standard unittest.mock.patch
    with patch('src.core.bootloader.requests.get') as mock_get:
        new_manifest = {
            "project_id": "TEST-PROJECT",
            "manifest_id": "MANIFEST-001",
            "pipeline_steps": []
        }
        # Mocking the response object
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = new_manifest
        mock_get.return_value = mock_response
        
        Bootloader.hydrate(state)
    
    updated_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert updated_ledger["metadata"]["project_id"] == "TEST-PROJECT"
    assert "old_step" not in updated_ledger["steps"]