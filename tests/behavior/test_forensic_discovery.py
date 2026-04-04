# tests/behavior/test_forensic_discovery.py

import json
import pytest
from src.core.state_engine import OrchestrationState
from src.core.constants import OrchestrationStatus

def test_gap_finder_transition_logic(tmp_path):
    """
    CONSTITUTION CHECK: Phase B (2) - The Forensic Discovery Gate.
    Verifies that the engine transitions from WAITING to DISPATCHED
    only when physical artifacts satisfy the 'requires' list.
    """
    # 1. SETUP: Seed Environment
    config_file = tmp_path / "disk.json"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    ledger_path = tmp_path / "ledger.json"
    
    config_file.write_text(json.dumps({
        "project_id": "FORENSIC-TEST",
        "manifest_url": "http://mock.com"
    }), encoding="utf-8")

    state = OrchestrationState(str(config_file), str(data_dir), str(ledger_path))

    # 2. DEFINE MANIFEST: Physics Step
    manifest = {
        "manifest_id": "M-NAV-01",
        "project_id": "FORENSIC-TEST",
        "pipeline_steps": [{
            "name": "navier_stokes_solver",
            "requires": ["geometry.msh"],
            "produces": ["results.zip"],
            "target_repo": "nomad/fluid-worker",
            "timeout_hours": 1
        }]
    }
    state.hydrate_manifest(manifest)

    # 3. SCENARIO A: Requirement Missing (Gap)
    ledger = {"navier_stokes_solver": {"status": OrchestrationStatus.WAITING.value}}
    state.reconcile_and_heal(ledger)
    assert ledger["navier_stokes_solver"]["status"] == OrchestrationStatus.WAITING.value
    
    # 4. SCENARIO B: Requirement Satisfied (Gap Closed)
    (data_dir / "geometry.msh").write_text("Mock mesh data")
    state.reconcile_and_heal(ledger)
    
    # Per reconcile_and_heal logic: If requirements met, transition to IN_PROGRESS/DISPATCHED
    assert ledger["navier_stokes_solver"]["status"] == OrchestrationStatus.IN_PROGRESS.value
    print("✅ Gap Finder Verified: Requirement presence triggered transition.")

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
    state.hydrate_manifest({
        "manifest_id": "M-COMP",
        "pipeline_steps": [{"name": "task_a", "requires": [], "produces": ["results.zip"]}]
    })

    # SCENARIO: Result file exists
    (data_dir / "results.zip").write_text("Mock results")
    ledger = {"task_a": {"status": OrchestrationStatus.IN_PROGRESS.value}}
    
    state.reconcile_and_heal(ledger)
    assert ledger["task_a"]["status"] == OrchestrationStatus.COMPLETED.value
    print("✅ Completion Gate Verified: Artifact presence closed the orchestration loop.")