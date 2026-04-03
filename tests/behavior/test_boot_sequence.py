import pytest
import json
import time
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Core Engine Imports
from src.core.bootloader import Bootloader
from src.core.state_engine import OrchestrationState
from src.core.constants import SystemPaths

@pytest.fixture
def boot_env():
    """
    Real-World Environment Fixture.
    Uses SystemPaths to align with the actual nomadic directory structure.
    """
    # 1. Map to Real Internal Paths
    config_dir = Path(SystemPaths.CONFIG_DIR)
    data_path = Path(SystemPaths.DATA_DIR)
    
    active_disk = config_dir / SystemPaths.ACTIVE_DISK
    dormant_flag = config_dir / SystemPaths.DORMANT_FLAG
    ledger_path = config_dir / SystemPaths.LEDGER
    
    # 2. Ensure directories exist for the test cycle
    config_dir.mkdir(parents=True, exist_ok=True)
    data_path.mkdir(parents=True, exist_ok=True)
    
    # 3. Ensure a valid active_disk exists for the loader to mount
    if not active_disk.exists():
        initial_config = {
            "project_id": "TEST-PROJECT",
            "manifest_url": "https://api.test/manifest",
            "active": True
        }
        active_disk.write_text(json.dumps(initial_config), encoding="utf-8")
    
    return {
        "config_dir": config_dir,
        "active_disk": active_disk,
        "dormant_flag": dormant_flag,
        "ledger_path": ledger_path,
        "data_path": data_path
    }

def test_clean_wakeup_mounting(boot_env):
    """
    Scenario: Clean Wake-Up
    Verifies that Bootloader.mount returns a valid OrchestrationState using real paths.
    """
    state = Bootloader.mount(
        str(boot_env["active_disk"]), 
        str(boot_env["data_path"]),
        str(boot_env["ledger_path"])
    )
    
    assert isinstance(state, OrchestrationState)
    assert state.project_id == "TEST-PROJECT"
    # Ensure type consistency (String vs Path)
    assert str(state.data_path) == str(boot_env["data_path"])

def test_auto_wake_logic(boot_env):
    """
    Scenario: Auto-Wake Trigger
    Verifies that a newer active_disk.json flips DORMANT to ACTIVE on the real disk.
    """
    dormant_path = boot_env["dormant_flag"]
    active_disk = boot_env["active_disk"]
    
    # 1. Force DORMANT state and anchor it 1 hour in the past
    dormant_path.write_text("STATUS: DORMANT", encoding="utf-8")
    past_time = time.time() - 3600
    os.utime(dormant_path, (past_time, past_time))
    
    # 2. Touch the active_disk to the 'Now' to trigger the comparison logic
    os.utime(active_disk, None) 
    
    # 3. Trigger Mount (The Logic Gate)
    Bootloader.mount(
        str(active_disk), 
        str(boot_env["data_path"]),
        str(boot_env["ledger_path"])
    )
    
    # 4. Verify Side-Effect on Disk
    time.sleep(0.1) # FS Sync buffer
    content = dormant_path.read_text(encoding="utf-8").strip().upper()
    
    assert "ACTIVE" in content, f"Engine failed to flip flag at {dormant_path}. Found: {content}"

def test_poisoned_manifest_schema_gate(boot_env):
    """
    Scenario: Poisoned Manifest (Schema Enforcement)
    Ensures that the real StateEngine prevents hydration if the schema is breached.
    """
    state = Bootloader.mount(
        str(boot_env["active_disk"]), 
        str(boot_env["data_path"]),
        str(boot_env["ledger_path"])
    )
    
    poisoned_data = {
        "manifest_id": "FAIL-001",
        "project_id": "POISON-PROJECT"
        # Missing required 'pipeline_steps' or other schema keys
    }
    
    with pytest.raises(RuntimeError) as excinfo:
        state.hydrate_manifest(poisoned_data)
    
    assert "Hard-Halt" in str(excinfo.value)

def test_missing_config_halt(boot_env):
    """
    Scenario: Missing Foundation
    Ensures Bootloader fails correctly if the active_disk is missing.
    """
    missing_path = boot_env["config_dir"] / "ghost_config.json"
    if missing_path.exists():
        os.remove(missing_path)
    
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
    Verifies that a shift in Project ID clears the local ledger artifacts.
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
    
    # Mocking the External API call only, keeping internal logic real
    with patch('src.core.bootloader.requests.get') as mock_get:
        new_manifest = {
            "project_id": "TEST-PROJECT",
            "manifest_id": "MANIFEST-001",
            "pipeline_steps": []
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = new_manifest
        mock_get.return_value = mock_response
        
        Bootloader.hydrate(state)
    
    # Verify the physical file was wiped and re-seeded
    updated_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert updated_ledger["metadata"]["project_id"] == "TEST-PROJECT"
    assert "old_step" not in updated_ledger["steps"]