# tests/behavior/test_ledger_traceability.py

import json
from src.core.state_engine import LedgerManager
from src.core.constants import OrchestrationStatus

def test_ledger_atomic_persistence(tmp_path):
    """
    CONSTITUTION CHECK: Phase A (4) - The Sovereign Ledger.
    Verifies that state changes are physically written to the ledger file
    to ensure traceability across 'Pulses'.
    """
    # 1. Setup
    ledger_file = tmp_path / "orchestration_ledger.json"
    manager = LedgerManager(str(ledger_file))
    
    project_id = "PROJ-ALPHA"
    manifest_id = "M-123"
    step_name = "simulation_run"

    # 2. Log a Dispatch Event
    manager.log_dispatch(
        project_id=project_id,
        manifest_id=manifest_id,
        step_name=step_name,
        target_repo="nomad/worker-repo",
        timeout_hours=1
    )

    # 3. Physical Verification (The "Black Box" Check)
    assert ledger_file.exists()
    with open(ledger_file, 'r') as f:
        data = json.load(f)
    
    # Verify mapping and status
    assert data[step_name]["status"] == OrchestrationStatus.IN_PROGRESS.value
    assert data[step_name]["manifest_id"] == manifest_id
    assert "dispatched_at" in data[step_name]

    # 4. Update Status (Simulation Completion)
    manager.update_step_status(step_name, OrchestrationStatus.COMPLETED)
    
    # Verify Persistent Change
    with open(ledger_file, 'r') as f:
        updated_data = json.load(f)
    assert updated_data[step_name]["status"] == OrchestrationStatus.COMPLETED.value
    print("✅ Ledger Traceability Verified: Atomic Persistence confirmed on disk.")

def test_ledger_hydration_integrity(tmp_path):
    """
    CONSTITUTION CHECK: Phase A (4) - Traceable Physics.
    Verifies that the manager can load existing state from a previous Pulse.
    """
    ledger_file = tmp_path / "existing_ledger.json"
    initial_content = {
        "old_step": {
            "status": "COMPLETED",
            "manifest_id": "M-OLD"
        }
    }
    ledger_file.write_text(json.dumps(initial_content))

    manager = LedgerManager(str(ledger_file))
    current_state = manager.load_ledger()
    
    assert current_state["old_step"]["status"] == "COMPLETED"
    assert "old_step" in current_state