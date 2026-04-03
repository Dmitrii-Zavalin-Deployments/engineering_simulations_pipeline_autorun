# tests/core/test_ledger_logic.py

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
    """Sets up a physical nomadic workspace for Ledger testing."""
    config_dir = tmp_path / SystemPaths.CONFIG_DIR
    config_dir.mkdir(parents=True)
    
    ledger_file = config_dir / SystemPaths.LEDGER
    audit_file = tmp_path / "performance_audit.md"
    
    # Initialize with the Forensic SSoT Structure
    initial_structure = {
        "metadata": {
            "project_id": "TEST-PROJ-V1",
            "manifest_id": "MANIFEST-V1"
        },
        "steps": {}
    }
    ledger_file.write_text(json.dumps(initial_structure), encoding="utf-8")
    audit_file.write_text("# 🛰️ Simulation Engine Performance Audit\n\n", encoding="utf-8")
    
    return {
        "root": tmp_path,
        "ledger": str(ledger_file),
        "audit": str(audit_file)
    }

def test_atomic_nested_update(nomadic_env):
    """
    Scenario: Update preserves metadata while nesting steps.
    Ensures that writing a step doesn't wipe the Project ID.
    """
    manager = LedgerManager(log_path=nomadic_env["audit"])
    # Point manager to the specific test ledger
    manager.orchestration_path = Path(nomadic_env["ledger"])
    
    manager.update_job_status(
        job_name="physics_solve",
        status=OrchestrationStatus.IN_PROGRESS.value,
        metadata={"target": "org/repo", "timeout_hours": 6}
    )
    
    data = json.loads(Path(nomadic_env["ledger"]).read_text())
    
    # Verify Forensic Identity
    assert data["metadata"]["project_id"] == "TEST-PROJ-V1"
    # Verify Step Nesting
    assert "physics_solve" in data["steps"]
    assert data["steps"]["physics_solve"]["status"] == OrchestrationStatus.IN_PROGRESS.value
    assert "last_triggered" in data["steps"]["physics_solve"]

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
    
    data = json.loads(Path(nomadic_env["ledger"]).read_text())
        
    assert data["metadata"]["project_id"] == "NEW-PROJECT-ID"
    assert data["metadata"]["manifest_id"] == "NEW-MANIFEST-ID"
    assert "geometry_gen" in data["steps"]

def test_audit_trail_atomic_prepending(nomadic_env):
    """
    Scenario: Verify Audit Log uses prepending (Newest First).
    Rule 5 Compliance: Operational Hygiene.
    """
    manager = LedgerManager(log_path=nomadic_env["audit"])
    
    manager.record_event("EVENT_ALPHA", "Message One")
    manager.record_event("EVENT_BETA", "Message Two")
    
    content = Path(nomadic_env["audit"]).read_text()
    
    # Newest (Beta) must be physically higher in the file than Oldest (Alpha)
    assert content.find("Message Two") < content.find("Message One")
    assert "# 🛰️ Simulation Engine Performance Audit" in content

def test_malformed_ledger_recovery(nomadic_env):
    """
    Scenario: Resilience against JSON corruption (Rule 4).
    """
    Path(nomadic_env["ledger"]).write_text("CORRUPTED_NON_JSON_DATA")
    
    manager = LedgerManager(log_path=nomadic_env["audit"])
    manager.orchestration_path = Path(nomadic_env["ledger"])
    
    state = manager.load_orchestration_state()
    
    assert "metadata" in state
    assert "steps" in state
    assert state["steps"] == {} # Should return clean slate

def test_identity_preservation_logic(nomadic_env):
    """
    Scenario: Same IDs -> No Wipe.
    If the manifest hasn't changed, we don't lose our 'IN_PROGRESS' markers.
    """
    state, data_path = StateEngineDummy.create(
        nomadic_env["root"], 
        project_id="TEST-PROJ-V1", 
        manifest_id="MANIFEST-V1"
    )
    
    # Pre-load ledger with a 'active' step
    ledger_path = Path(nomadic_env["ledger"])
    initial_data = {
        "metadata": {"project_id": "TEST-PROJ-V1", "manifest_id": "MANIFEST-V1"},
        "steps": {"existing_job": {"status": "IN_PROGRESS"}}
    }
    ledger_path.write_text(json.dumps(initial_data))

    # Mock remote manifest with same IDs
    with patch("src.core.bootloader.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "project_id": "TEST-PROJ-V1",
            "manifest_id": "MANIFEST-V1",
            "pipeline_steps": []
        }
        Bootloader.hydrate(state)

    # Verification: 'existing_job' was NOT wiped
    updated = json.loads(ledger_path.read_text())
    assert "existing_job" in updated["steps"]

@pytest.mark.parametrize("new_pid, new_mid", [
    ("DIFFERENT-PID", "MANIFEST-V1"),
    ("TEST-PROJ-V1", "DIFFERENT-MID"),
    ("NEW-PID", "NEW-MID"),
])
def test_identity_mismatch_forensic_reset(nomadic_env, new_pid, new_mid):
    """
    Scenario: Identity Shift -> Atomic Wipe.
    If either ID changes, we wipe 'steps' to prevent nomadic cross-pollution.
    """
    state, data_path = StateEngineDummy.create(nomadic_env["root"])
    ledger_path = Path(nomadic_env["ledger"])
    
    # 1. Setup ledger with 'old' data
    initial_data = {
        "metadata": {"project_id": "OLD-P", "manifest_id": "OLD-M"},
        "steps": {"poison_step": {"status": "COMPLETED"}}
    }
    ledger_path.write_text(json.dumps(initial_data))

    # 2. Hydrate with the parametrized 'new' IDs
    with patch("src.core.bootloader.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "project_id": new_pid,
            "manifest_id": new_mid,
            "pipeline_steps": []
        }
        Bootloader.hydrate(state)

    # 3. Assert: 'poison_step' is GONE
    updated = json.loads(ledger_path.read_text())
    assert "poison_step" not in updated["steps"]
    assert updated["metadata"]["project_id"] == new_pid
    assert updated["metadata"]["manifest_id"] == new_mid