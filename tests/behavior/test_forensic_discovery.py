# tests/behavior/test_forensic_discovery.py

import json
from src.core.state_engine import OrchestrationState
from src.core.constants import OrchestrationStatus

def test_gap_finder_transition_logic(tmp_path):
    """
    CONSTITUTION CHECK: Phase B (2) - The Forensic Discovery Gate.
    Verifies that the engine transitions to PENDING when inputs exist.
    """
    # 1. SETUP: Seed Environment
    config_file = tmp_path / "disk.json"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    config_file.write_text(json.dumps({
        "project_id": "GAP-TEST",
        "manifest_url": "http://mock.com"
    }), encoding="utf-8")

    state = OrchestrationState(str(config_file), str(data_dir), str(tmp_path/"ledger.json"))

    # 2. DEFINE VALID MANIFEST: Physics Step
    manifest = {
        "manifest_id": "M-NAV-01",
        "project_id": "GAP-TEST",
        "pipeline_steps": [{
            "name": "navier_stokes_solver",
            "requires": ["geometry.msh"],
            "produces": ["results.zip"],
            "target_repo": "nomad/fluid-worker",
            "timeout_hours": 1
        }]
    }
    state.hydrate_manifest(manifest)

    # 3. SCENARIO: Requirement Satisfied -> Transition to PENDING
    (data_dir / "geometry.msh").write_text("Mock mesh")
    ledger = {"navier_stokes_solver": {"status": OrchestrationStatus.WAITING.value}}
    
    state.reconcile_and_heal(ledger)
    
    # Engine logic: Inputs present but outputs missing = PENDING (Ready to Fire)
    assert ledger["navier_stokes_solver"]["status"] == OrchestrationStatus.PENDING.value
    print("✅ Gap Finder Verified: Requirement presence triggered PENDING state.")

def test_forensic_completion_gate(tmp_path):
    """
    CONSTITUTION CHECK: Phase B (2) - Cycle Completion.
    Verifies that the presence of 'produces' artifacts marks the step as COMPLETED.
    """
    config_file = tmp_path / "disk.json"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    config_file.write_text(json.dumps({"project_id": "COMP-TEST", "manifest_url": "url"}), encoding="utf-8")
    
    state = OrchestrationState(str(config_file), str(data_dir), str(tmp_path/"ledger.json"))
    
    # FIX: Added 'target_repo' and 'project_id' to satisfy Schema Sovereignty
    state.hydrate_manifest({
        "manifest_id": "M-COMP",
        "project_id": "COMP-TEST",
        "pipeline_steps": [{
            "name": "task_a", 
            "requires": [], 
            "produces": ["results.zip"],
            "target_repo": "nomad/completion-worker"
        }]
    })

    # SCENARIO: Output exists -> Transition to COMPLETED
    (data_dir / "results.zip").write_text("Mock results")
    ledger = {"task_a": {"status": OrchestrationStatus.PENDING.value}}
    
    state.reconcile_and_heal(ledger)
    assert ledger["task_a"]["status"] == OrchestrationStatus.COMPLETED.value
    print("✅ Completion Gate Verified: Artifact presence triggered COMPLETED state.")