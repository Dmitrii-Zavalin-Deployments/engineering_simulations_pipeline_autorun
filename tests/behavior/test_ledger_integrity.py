# tests/behavior/test_ledger_integrity.py

import pytest
import json
import os
from pathlib import Path

# Internal Core Imports
from src.core.update_ledger import LedgerManager
from src.core.bootloader import Bootloader
from src.core.constants import SystemPaths, OrchestrationStatus
from tests.helpers.state_engine_dummy import StateEngineDummy

@pytest.fixture
def nomadic_env(tmp_path):
    """
    Physical Environment Fixture.
    Creates real subdirectories and local manifest files on disk.
    NO MOCKS ALLOWED.
    """
    # 1. Setup Physical Root
    root = tmp_path / "engine_node"
    config_dir = root / SystemPaths.CONFIG_DIR
    config_dir.mkdir(parents=True)
    
    ledger_path = config_dir / SystemPaths.LEDGER
    audit_path = root / "performance_audit.md"
    
    # 2. Seed Initial Physical State
    initial_ledger = {
        "metadata": {
            "project_id": "INIT-PROJ",
            "manifest_id": "MANIFEST-V1"
        },
        "steps": {}
    }
    ledger_path.write_text(json.dumps(initial_ledger), encoding="utf-8")
    
    # 3. Create a REAL local manifest for "remote" simulation
    manifest_path = root / "mock_remote_manifest.json"
    
    return {
        "root": root, 
        "ledger": ledger_path,
        "audit": audit_path,
        "manifest_file": manifest_path,
        "init_pid": "INIT-PROJ",
        "init_mid": "MANIFEST-V1"
    }

def test_metadata_handshake_dispatch(nomadic_env):
    """Scenario: Verify log_dispatch updates physical global identity."""
    manager = LedgerManager(log_path=str(nomadic_env["audit"]))
    manager.orchestration_path = str(nomadic_env["ledger"])
    
    manager.log_dispatch(
        project_id="NEW-PROJECT-ID",
        manifest_id="NEW-MANIFEST-ID",
        step_name="geometry_gen",
        target_repo="org/geom",
        timeout_hours=2
    )
    
    data = json.loads(nomadic_env["ledger"].read_text(encoding="utf-8"))
    
    assert data["metadata"]["project_id"] == "NEW-PROJECT-ID"
    assert data["metadata"]["manifest_id"] == "NEW-MANIFEST-ID"

def test_audit_trail_atomic_prepending(nomadic_env):
    """Scenario: Verify Audit Log physical prepending (Newest First)."""
    manager = LedgerManager(log_path=str(nomadic_env["audit"]))
    
    manager.record_event("EVENT_ALPHA", "Message One")
    manager.record_event("EVENT_BETA", "Message Two")
    
    content = nomadic_env["audit"].read_text()
    
    # Message Two (Beta) must appear before Message One (Alpha) in the byte stream
    assert content.find("Message Two") < content.find("Message One")

def test_malformed_ledger_recovery(nomadic_env):
    """Scenario: Physical Resilience against JSON corruption on disk."""
    nomadic_env["ledger"].write_text("!!CRITICAL_HARDWARE_FAILURE_NON_JSON!!")
    
    manager = LedgerManager(log_path=str(nomadic_env["audit"]))
    manager.orchestration_path = str(nomadic_env["ledger"])
    
    state = manager.load_orchestration_state()
    
    assert "metadata" in state
    assert state["steps"] == {}

@pytest.mark.parametrize("new_pid, new_mid", [
    ("DIFFERENT-PID", "MANIFEST-V1"),
    ("INIT-PROJ", "DIFFERENT-MID"),
    ("NEW-PID", "NEW-MID"),
])
def test_identity_mismatch_forensic_reset(nomadic_env, new_pid, new_mid):
    """
    Scenario: Identity Shift -> Atomic Wipe.
    Uses REAL file writes to verify the 'poison_step' is physically deleted.
    """
    # 1. Setup State and Point to Local Manifest
    state, _ = StateEngineDummy.create(nomadic_env["root"])
    
    manifest_content = {
        "project_id": new_pid,
        "manifest_id": new_mid,
        "pipeline_steps": [
            {"name": "fresh_start", "target_repo": "org/new", "timeout_hours": 24}
        ]
    }
    nomadic_env["manifest_file"].write_text(json.dumps(manifest_content))
    
    # Inject physical local path into the state
    state.manifest_url = f"file://{nomadic_env['manifest_file'].absolute()}"
    state.ledger_path = nomadic_env["ledger"]

    # 2. Write Poison Step
    initial_data = {
        "metadata": {"project_id": nomadic_env["init_pid"], "manifest_id": nomadic_env["init_mid"]},
        "steps": {"poison_step": {"status": "COMPLETED"}}
    }
    nomadic_env["ledger"].write_text(json.dumps(initial_data))

    # 3. Hydrate (This uses requests-file or local read logic)
    # If the environment doesn't support file://, we bypass requests.get in Bootloader 
    # and call _validate_integrity + seeding logic directly.
    Bootloader.hydrate(state)

    # 4. Forensic Check
    updated = json.loads(nomadic_env["ledger"].read_text())
    assert "poison_step" not in updated["steps"], f"Atomic wipe failed for {new_pid}"
    assert "fresh_start" in updated["steps"]
    assert updated["metadata"]["project_id"] == new_pid