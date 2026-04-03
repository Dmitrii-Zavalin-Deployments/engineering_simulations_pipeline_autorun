# tests/behavior/test_boot_sequence.py

import pytest
import json
import time
import os
import requests_mock
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
    # ALIGNMENT: Passing the 3rd required argument (ledger_path)
    state = Bootloader.mount(
        str(boot_env["active_disk"]), 
        str(boot_env["data_path"]),
        str(boot_env["ledger_path"])
    )
    
    assert isinstance(state, OrchestrationState)
    assert state.project_id == "TEST-PROJECT"
    assert state.data_path == str(boot_env["data_path"])

def test_auto_wake_logic(boot_env):
    """
    Scenario: Auto-Wake Trigger
    Verifies that a newer active_disk.json flips DORMANT to ACTIVE.
    """
    # 1. Set engine to DORMANT
    boot_env["dormant_flag"].write_text("STATUS: DORMANT", encoding="utf-8")
    
    # 2. Ensure active_disk has a newer timestamp (Shift forward 2 seconds)
    new_time = time.time() + 2
    os.utime(boot_env["active_disk"], (new_time, new_time))
    
    # 3. Mount (3-way handshake)
    Bootloader.mount(
        str(boot_env["active_disk"]), 
        str(boot_env["data_path"]),
        str(boot_env["ledger_path"])
    )
    
    # 4. Assert: Status is now ACTIVE
    content = boot_env["dormant_flag"].read_text(encoding="utf-8")
    assert "ACTIVE" in content

def test_poisoned_manifest_schema_gate(boot_env):
    """
    Scenario: Poisoned Manifest (Schema Enforcement)
    Verifies that a malformed manifest triggers a Hard-Halt during hydration.
    """
    # ALIGNMENT: 3-way handshake
    state = Bootloader.mount(
        str(boot_env["active_disk"]), 
        str(boot_env["data_path"]),
        str(boot_env["ledger_path"])
    )
    
    # Poisoned data: missing mandatory 'pipeline_steps'
    poisoned_data = {
        "manifest_id": "FAIL-001",
        "project_id": "POISON-PROJECT"
    }
    
    # We expect a RuntimeError because hydrate_manifest wraps the ValidationError 
    with pytest.raises(RuntimeError) as excinfo:
        state.hydrate_manifest(poisoned_data)
    
    assert "Hard-Halt" in str(excinfo.value)

def test_missing_config_halt(boot_env):
    """
    Scenario: Missing Foundation
    Engine must raise RuntimeError if active_disk.json is not found.
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
    # 1. Create a "stale" ledger for a different project
    ledger_path = boot_env["ledger_path"]
    stale_ledger = {
        "metadata": {"project_id": "OLD-PROJECT", "manifest_id": "OLD-MID"},
        "steps": {"old_step": {"status": "COMPLETED"}}
    }
    ledger_path.write_text(json.dumps(stale_ledger), encoding="utf-8")
    
    # 2. Setup state
    state = Bootloader.mount(
        str(boot_env["active_disk"]), 
        str(boot_env["data_path"]),
        str(ledger_path)
    )
    
    # 3. Hydrate with NEW manifest IDs (from the dummy: TEST-PROJECT / MANIFEST-001)
    with requests_mock.Mocker() as m:
        new_manifest = {
            "project_id": "TEST-PROJECT",
            "manifest_id": "MANIFEST-001",
            "pipeline_steps": []
        }
        m.get(state.manifest_url, json=new_manifest)
        
        Bootloader.hydrate(state)
    
    # 4. Verify Ledger was wiped and updated with new IDs
    updated_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert updated_ledger["metadata"]["project_id"] == "TEST-PROJECT"
    assert "old_step" not in updated_ledger["steps"]