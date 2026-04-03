# tests/behavior/test_ledger_integrity.py

import pytest
import json
from pathlib import Path
from unittest.mock import patch

# Internal Core Imports
from src.core.update_ledger import LedgerManager
from src.core.bootloader import Bootloader
from src.core.constants import SystemPaths, OrchestrationStatus
from tests.helpers.state_engine_dummy import StateEngineDummy

@pytest.fixture
def nomadic_env(tmp_path):
    """
    Unified Environment Fixture.
    Provides real-world paths AND a 'root' for dummy factory compatibility.
    """
    config_dir = Path(SystemPaths.CONFIG_DIR)
    ledger_path = config_dir / SystemPaths.LEDGER
    audit_path = Path("performance_audit.md")
    
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Standardize the starting state for deterministic tests
    initial_ledger = {
        "metadata": {
            "project_id": "INIT-PROJ",
            "manifest_id": "MANIFEST-V1"
        },
        "steps": {}
    }
    ledger_path.write_text(json.dumps(initial_ledger), encoding="utf-8")
    
    return {
        "root": tmp_path, 
        "ledger": str(ledger_path),
        "audit": str(audit_path),
        "init_pid": "INIT-PROJ",
        "init_mid": "MANIFEST-V1"
    }

def test_metadata_handshake_dispatch(nomadic_env):
    """
    Scenario: log_dispatch updates global identity metadata.
    """
    manager = LedgerManager(log_path=nomadic_env["audit"])
    manager.orchestration_path = Path(nomadic_env["ledger"])
    
    manager.log_dispatch(
        project_id="NEW-PROJECT-ID",
        manifest_id="NEW-MANIFEST-ID",
        step_name="geometry_gen",
        target_repo="org/geom",
        timeout_hours=2
    )
    
    data = json.loads(Path(nomadic_env["ledger"]).read_text(encoding="utf-8"))
    
    assert data["metadata"]["project_id"] == "NEW-PROJECT-ID"
    # NOTE: If this fails, ensure src/core/update_ledger.py assigns manifest_id
    assert data["metadata"]["manifest_id"] == "NEW-MANIFEST-ID"

def test_atomic_nested_update(nomadic_env):
    """
    Scenario: Update preserves metadata while nesting steps.
    """
    manager = LedgerManager(log_path=nomadic_env["audit"])
    manager.orchestration_path = Path(nomadic_env["ledger"])
    
    manager.update_job_status(
        job_name="physics_solve",
        status=OrchestrationStatus.IN_PROGRESS.value,
        metadata={"target": "org/repo", "timeout_hours": 6}
    )
    
    data = json.loads(Path(nomadic_env["ledger"]).read_text())
    
    # Assert against the fixture's initial state to ensure preservation
    assert data["metadata"]["project_id"] == nomadic_env["init_pid"]
    assert "physics_solve" in data["steps"]
    assert data["steps"]["physics_solve"]["status"] == OrchestrationStatus.IN_PROGRESS.value

def test_audit_trail_atomic_prepending(nomadic_env):
    """
    Scenario: Verify Audit Log uses prepending (Newest First).
    """
    manager = LedgerManager(log_path=nomadic_env["audit"])
    
    manager.record_event("EVENT_ALPHA", "Message One")
    manager.record_event("EVENT_BETA", "Message Two")
    
    content = Path(nomadic_env["audit"]).read_text()
    
    # Newest (Beta) must be physically higher in the file than Oldest (Alpha)
    assert content.find("Message Two") < content.find("Message One")

def test_malformed_ledger_recovery(nomadic_env):
    """
    Scenario: Resilience against JSON corruption.
    """
    Path(nomadic_env["ledger"]).write_text("CORRUPTED_NON_JSON_DATA")
    
    manager = LedgerManager(log_path=nomadic_env["audit"])
    manager.orchestration_path = Path(nomadic_env["ledger"])
    
    state = manager.load_orchestration_state()
    
    assert "metadata" in state
    assert state["steps"] == {}

def test_identity_preservation_logic(nomadic_env):
    """
    Scenario: Same IDs -> No Wipe.
    """
    state, data_path = StateEngineDummy.create(
        nomadic_env["root"], 
        project_id=nomadic_env["init_pid"], 
        manifest_id=nomadic_env["init_mid"]
    )
    
    ledger_path = Path(nomadic_env["ledger"])
    initial_data = {
        "metadata": {"project_id": nomadic_env["init_pid"], "manifest_id": nomadic_env["init_mid"]},
        "steps": {"existing_job": {"status": "IN_PROGRESS"}}
    }
    ledger_path.write_text(json.dumps(initial_data))

    with patch("src.core.bootloader.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "project_id": nomadic_env["init_pid"],
            "manifest_id": nomadic_env["init_mid"],
            "pipeline_steps": []
        }
        Bootloader.hydrate(state)

    updated = json.loads(ledger_path.read_text())
    assert "existing_job" in updated["steps"]

@pytest.mark.parametrize("new_pid, new_mid", [
    ("DIFFERENT-PID", "MANIFEST-V1"),
    ("INIT-PROJ", "DIFFERENT-MID"),
    ("NEW-PID", "NEW-MID"),
])
def test_identity_mismatch_forensic_reset(nomadic_env, new_pid, new_mid):
    """
    Scenario: Identity Shift -> Atomic Wipe.
    """
    state, data_path = StateEngineDummy.create(nomadic_env["root"])
    ledger_path = Path(nomadic_env["ledger"])
    
    initial_data = {
        "metadata": {"project_id": nomadic_env["init_pid"], "manifest_id": nomadic_env["init_mid"]},
        "steps": {"poison_step": {"status": "COMPLETED"}}
    }
    ledger_path.write_text(json.dumps(initial_data))

    with patch("src.core.bootloader.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "project_id": new_pid,
            "manifest_id": new_mid,
            "pipeline_steps": []
        }
        Bootloader.hydrate(state)

    updated = json.loads(ledger_path.read_text())
    assert "poison_step" not in updated["steps"]
    assert updated["metadata"]["project_id"] == new_pid