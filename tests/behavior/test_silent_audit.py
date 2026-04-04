# tests/behavior/test_silent_audit.py

import json
import pytest
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
    
    step_name = "audit_step"
    state.hydrate_manifest({
        "manifest_id": "M-AUDIT",
        "project_id": "AUDIT-PROJ-01",
        "pipeline_steps": [{
            "name": step_name,
            "requires": ["input.txt"],
            "produces": ["output.txt"],
            "target_repo": "nomad/audit-worker"
        }]
    })

    # 2. INITIAL STATE: Create a WAITING ledger
    initial_ledger = {step_name: {"status": OrchestrationStatus.WAITING.value}}
    
    # 3. ACTION: Close the gap (Physics) and Reconcile (Logic)
    (data_dir / "input.txt").write_text("Triggering audit...")
    
    # This call triggers the internal save to ledger_path (Forensic Line 106)
    state.reconcile_and_heal(initial_ledger)

    # 4. VERIFICATION: The "Silent Operator" Audit
    assert ledger_path.exists(), "❌ FAIL: Ledger was not persisted to disk."
    
    with open(ledger_path, 'r', encoding="utf-8") as f:
        disk_data = json.load(f)
        
    # ALIGNMENT: Check root or 'steps' wrapper (Forensic Line 101)
    actual_ledger = disk_data.get("steps", disk_data)
    
    assert step_name in actual_ledger, f"❌ KeyError: {step_name} missing from disk. Found: {list(disk_data.keys())}"
    assert actual_ledger[step_name]["status"] == OrchestrationStatus.PENDING.value
    
    print(f"✅ Audit Gate Verified: Ledger on disk reflects PENDING state.")

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
    
    step_name = "step_x"
    state.hydrate_manifest({
        "manifest_id": "M-TRACE",
        "project_id": "TRACE",
        "pipeline_steps": [{"name": step_name, "requires": [], "produces": ["final.zip"], "target_repo": "x"}]
    })

    # Scenario: Final artifact appears
    (data_dir / "final.zip").write_text("End of run")
    ledger = {step_name: {"status": OrchestrationStatus.PENDING.value}}
    
    state.reconcile_and_heal(ledger)
    
    # Verify Disk Integrity
    with open(ledger_path, 'r', encoding="utf-8") as f:
        disk_data = json.load(f)
    
    actual_ledger = disk_data.get("steps", disk_data)
    assert actual_ledger[step_name]["status"] == OrchestrationStatus.COMPLETED.value
    print("✅ Traceability Verified: COMPLETED state persisted to nomadic ledger.")