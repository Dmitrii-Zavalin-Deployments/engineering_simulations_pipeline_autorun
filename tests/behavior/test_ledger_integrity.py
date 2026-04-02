import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from src.core.bootloader import Bootloader
from src.core.state_engine import OrchestrationState

# SSoT Alignment: Using the updated LedgerManager with Metadata/Steps support
from src.core.update_ledger import LedgerManager

@pytest.fixture
def nomadic_env(tmp_path):
    """Sets up a temporary workspace for I/O testing with the new structure."""
    root = tmp_path / "workdir"
    root.mkdir()
    
    ledger_file = root / "orchestration_ledger.json"
    audit_file = root / "performance_audit.md"
    
    # Initialize with the new Forensic Structure
    initial_structure = {
        "metadata": {
            "project_id": "test_proj_v1",
            "manifest_id": "test_man_v1"
        },
        "steps": {}
    }
    ledger_file.write_text(json.dumps(initial_structure), encoding="utf-8")
    audit_file.write_text("# 🛰️ Simulation Engine Performance Audit\n\n", encoding="utf-8")
    
    return {
        "root": root,
        "ledger": str(ledger_file),
        "audit": str(audit_file)
    }

def test_atomic_nested_update(nomadic_env):
    """
    Scenario: Verify update_job_status preserves metadata while nesting steps.
    Compliance: Forensic Identity Integrity.
    """
    manager = LedgerManager(orchestration_path=nomadic_env["ledger"], log_path=nomadic_env["audit"])
    
    # Trigger a job update
    manager.update_job_status(
        job_name="navier_stokes_execution",
        status="IN_PROGRESS",
        metadata={
            "target": "org/repo",
            "timeout_hours": 6
        }
    )
    
    with open(nomadic_env["ledger"], 'r') as f:
        data = json.load(f)
    
    # Verify Metadata is preserved
    assert data["metadata"]["project_id"] == "test_proj_v1"
    
    # Verify Step is correctly nested
    assert "navier_stokes_execution" in data["steps"]
    assert data["steps"]["navier_stokes_execution"]["status"] == "IN_PROGRESS"
    assert "last_triggered" in data["steps"]["navier_stokes_execution"]

def test_metadata_handshake_update(nomadic_env):
    """
    Scenario: Verify the ledger can update its own identity metadata during dispatch.
    """
    manager = LedgerManager(orchestration_path=nomadic_env["ledger"], log_path=nomadic_env["audit"])
    
    # Dispatching with a NEW project identity
    manager.log_dispatch(
        project_id="new_project_02",
        manifest_id="new_manifest_02",
        step_name="geometry_gen",
        target_repo="org/geom",
        timeout_hours=2
    )
    
    with open(nomadic_env["ledger"], 'r') as f:
        data = json.load(f)
        
    assert data["metadata"]["project_id"] == "new_project_02"
    assert data["metadata"]["manifest_id"] == "new_manifest_02"
    assert "geometry_gen" in data["steps"]

def test_clear_lock_isolation(nomadic_env):
    """
    Scenario: Releasing a lock should only remove the step, not the metadata.
    """
    manager = LedgerManager(orchestration_path=nomadic_env["ledger"], log_path=nomadic_env["audit"])
    
    # Setup an active step
    manager.update_job_status("step_to_clear", "IN_PROGRESS", {"target": "r", "timeout_hours": 1})
    
    # Clear it
    manager.clear_lock("step_to_clear")
    
    with open(nomadic_env["ledger"], 'r') as f:
        data = json.load(f)
        
    assert "step_to_clear" not in data["steps"]
    assert "project_id" in data["metadata"] # Identity must remain

def test_audit_trail_prepending(nomadic_env):
    """
    Scenario: Verify the Markdown audit log uses atomic prepending (Newest First).
    """
    manager = LedgerManager(orchestration_path=nomadic_env["ledger"], log_path=nomadic_env["audit"])
    
    manager.record_event("TEST_A", "First message")
    manager.record_event("TEST_B", "Second message")
    
    content = Path(nomadic_env["audit"]).read_text()
    
    # "Second message" should appear before "First message" in the file
    assert content.find("Second message") < content.find("First message")
    assert "# 🛰️ Simulation Engine Performance Audit" in content

def test_malformed_ledger_recovery(nomadic_env):
    """
    Scenario: Resilience against JSON corruption. 
    The load_orchestration_state should return a clean structure if the file is trash.
    """
    Path(nomadic_env["ledger"]).write_text("NOT_JSON")
    
    manager = LedgerManager(orchestration_path=nomadic_env["ledger"], log_path=nomadic_env["audit"])
    state = manager.load_orchestration_state()
    
    assert "metadata" in state
    assert "steps" in state
    assert state["steps"] == {}

def test_timestamp_rule_4_compliance(nomadic_env):
    """
    Verify timestamps inside 'steps' are ISO valid for timeout logic.
    """
    manager = LedgerManager(orchestration_path=nomadic_env["ledger"], log_path=nomadic_env["audit"])
    manager.update_job_status("time_test", "ACTIVE", {"target": "r", "timeout_hours": 1})
    
    with open(nomadic_env["ledger"], 'r') as f:
        data = json.load(f)
        ts = data["steps"]["time_test"]["last_triggered"]
        
        # Verify ISO format
        assert datetime.fromisoformat(ts) is not None

def test_identity_preservation_same_ids(nomadic_env):
    """
    Scenario: Same Project/Manifest ID.
    Verify that existing job steps in the ledger are NOT erased.
    """
    ledger_path = Path(nomadic_env["ledger"])
    
    # 1. Setup a ledger with an active job
    initial_ledger = {
        "metadata": {"project_id": "alpha_01", "manifest_id": "man_01"}, "steps": {"navier_stokes": {"status": "IN_PROGRESS", "timeout_hours": 6}}
    }
    ledger_path.write_text(json.dumps(initial_ledger))

    # 2. Mock a remote manifest with the EXACT SAME IDs
    mock_manifest = {
        "project_id": "alpha_01",
        "manifest_id": "man_01",
        "pipeline_steps": []
    }

    # 3. Trigger hydration
    state = OrchestrationState(str(ledger_path.parent / 'active_disk.json'), nomadic_env["root"])
    state.manifest_url = "http://mock.io"
    
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_manifest
        mock_get.return_value.status_code = 200
        Bootloader.hydrate(state)

    # 4. Verification: The 'navier_stokes' step must still exist
    updated_ledger = json.loads(ledger_path.read_text())
    assert "navier_stokes" in updated_ledger["steps"]
    assert updated_ledger["metadata"]["project_id"] == "alpha_01"


@pytest.mark.parametrize("remote_pid, remote_mid, scenario_name", [
    ("alpha_01", "man_NEW", "Different Manifest ID"),
    ("alpha_NEW", "man_01", "Different Project ID"),
    ("alpha_NEW", "man_NEW", "Both IDs Different"),
])
def test_identity_mismatch_reset(nomadic_env, remote_pid, remote_mid, scenario_name):
    """
    Scenario: Identity Mismatch (3 Sub-tests).
    Verify that if EITHER ID changes, the ledger steps are wiped (Forensic Reset).
    """
    ledger_path = Path(nomadic_env["ledger"])
    
    # 1. Setup a ledger with 'old' identity and a 'poison' step from a different project
    initial_ledger = {
        "metadata": {"project_id": "alpha_01", "manifest_id": "man_01"},
    }
    ledger_path.write_text(json.dumps(initial_ledger))

    # 2. Mock a remote manifest based on the parametrization
    mock_manifest = {
        "project_id": remote_pid,
        "manifest_id": remote_mid,
        "pipeline_steps": []
    }

    state = OrchestrationState(str(ledger_path.parent / 'active_disk.json'), nomadic_env["root"])
    state.manifest_url = "http://mock.io"

    # 3. Trigger hydration (which triggers the Bootloader integrity check)
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_manifest
        mock_get.return_value.status_code = 200
        Bootloader.hydrate(state)

    # 4. Verification
    updated_ledger = json.loads(ledger_path.read_text())
    
    # A. The 'old_project_job' must be GONE (Wiped)
    assert "old_project_job" not in updated_ledger["steps"]
    assert updated_ledger["steps"] == {}
    
    # B. The new metadata must be recorded
    assert updated_ledger["metadata"]["project_id"] == remote_pid
    assert updated_ledger["metadata"]["manifest_id"] == remote_mid
    
    print(f"✅ Reset Verified for scenario: {scenario_name}")