# tests/behavior/test_silent_audit.py

import json
from src.core.state_engine import OrchestrationState
from src.core.constants import OrchestrationStatus

def test_atomic_persistence_audit(tmp_path):
    """
    CONSTITUTION CHECK: Phase B (4) - The Silent Operator Audit Gate.
    Verifies that the ledger is physically updated on disk 
    immediately following a state reconciliation.
    """
    # 1. SETUP: Environment
    config_file = tmp_path / "disk.json"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    ledger_path = tmp_path / "orchestration_ledger.json" # The Audit Target
    
    config_file.write_text(json.dumps({
        "project_id": "AUDIT-PROJ-01",
        "manifest_url": "http://mock.com"
    }), encoding="utf-8")

    state = OrchestrationState(str(config_file), str(data_dir), str(ledger_path))
    
    # Define Manifest
    state.hydrate_manifest({
        "manifest_id": "M-AUDIT",
        "project_id": "AUDIT-PROJ-01",
        "pipeline_steps": [{
            "name": "audit_step",
            "requires": ["input.txt"],
            "produces": ["output.txt"],
            "target_repo": "nomad/audit-worker"
        }]
    })

    # 2. INITIAL STATE: Create a WAITING ledger
    initial_ledger = {"audit_step": {"status": OrchestrationStatus.WAITING.value}}
    
    # 3. ACTION: Close the gap (Physics) and Reconcile (Logic)
    (data_dir / "input.txt").write_text("Triggering audit...")
    
    # This call must trigger an internal save to ledger_path
    state.reconcile_and_heal(initial_ledger)

    # 4. VERIFICATION: The "Silent Operator" Audit
    # We don't just check the 'initial_ledger' dict; we check the physical DISK.
    assert ledger_path.exists(), "❌ FAIL: Ledger was not persisted to disk."
    
    with open(ledger_path, 'r', encoding="utf-8") as f:
        persisted_data = json.load(f)
        
    actual_status = persisted_data["audit_step"]["status"]
    assert actual_status == OrchestrationStatus.PENDING.value
    
    print("✅ Audit Gate Verified: Ledger on disk reflects PENDING state.")

def test_audit_traceability_sequence(tmp_path):
    """
    Verifies that completion is also tracked atomically.
    """
    config_file = tmp_path / "disk.json"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    ledger_path = tmp_path / "orchestration_ledger.json"
    
    config_file.write_text(json.dumps({"project_id": "TRACE", "manifest_url": "url"}), encoding="utf-8")
    state = OrchestrationState(str(config_file), str(data_dir), str(ledger_path))
    state.hydrate_manifest({
        "manifest_id": "M-TRACE",
        "project_id": "TRACE",
        "pipeline_steps": [{"name": "step_x", "requires": [], "produces": ["final.zip"], "target_repo": "x"}]
    })

    # Scenario: Final artifact appears
    (data_dir / "final.zip").write_text("End of run")
    ledger = {"step_x": {"status": OrchestrationStatus.PENDING.value}}
    
    state.reconcile_and_heal(ledger)
    
    # Verify Disk Integrity
    with open(ledger_path, 'r', encoding="utf-8") as f:
        disk_ledger = json.load(f)
    
    assert disk_ledger["step_x"]["status"] == OrchestrationStatus.COMPLETED.value
    print("✅ Traceability Verified: COMPLETED state persisted to nomadic ledger.")