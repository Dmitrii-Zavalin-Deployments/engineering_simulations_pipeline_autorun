# tests/behavior/test_orchestration_mechanism.py

import json
from src.core.bootloader import Bootloader
from src.core.state_engine import OrchestrationState

def test_mechanism_sovereignty_mount(tmp_path):
    """
    CONSTITUTION CHECK: Phase B - System Verification Tiers.
    Verifies the 'Mechanism': The Bootloader must successfully mount 
    the project configuration and initialize the OrchestrationState.
    """
    # 1. Setup Mock "Disc" (The Mechanism)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    ledger_path = tmp_path / "ledger.json"
    
    config_file = config_dir / "active_disk.json"
    config_file.write_text(json.dumps({
        "project_id": "MECHANISM-TEST",
        "manifest_url": "http://mock-cloud.com/manifest.json"
    }), encoding="utf-8")

    # 2. Execute Mount (The Logic Gate)
    # We pass the paths directly as the Bootloader.mount expects strings/Paths
    state = Bootloader.mount(str(config_file), str(data_dir), str(ledger_path))

    # 3. Verification
    assert isinstance(state, OrchestrationState)
    assert state.project_id == "MECHANISM-TEST"
    assert state.data_path == data_dir
    
    # Verify 'Physics' Independence: 
    # The engine is mounted and ready even though the data directory is empty.
    assert len(list(data_dir.iterdir())) == 0
    print("✅ Mechanism Sovereignty Verified: Bootloader mounted logic independently of physics.")

def test_agnostic_gap_identification(tmp_path):
    """
    CONSTITUTION CHECK: Phase B - Artifact Gap Identification.
    Verifies that the state engine identifies missing artifacts (The Gap) 
    solely based on presence, satisfying the 'Mechanism' rule.
    """
    # Setup state with a manual manifest
    state = OrchestrationState(
        config_path=str(tmp_path/"disk.json"), 
        data_root=str(tmp_path/"data"), 
        ledger_path=str(tmp_path/"ledger.json")
    )
    
    # Define a step that requires an artifact that doesn't exist
    manifest = {
        "manifest_id": "M-GAP",
        "pipeline_steps": [{
            "name": "solver_x",
            "requires": ["missing_physics.dat"],
            "produces": ["result.zip"]
        }]
    }
    state.manifest_data = manifest
    
    # Check status - should stay WAITING because the requirement is missing
    ledger = {"solver_x": {"status": "WAITING"}}
    state.reconcile_and_heal(ledger)
    
    assert ledger["solver_x"]["status"] == "WAITING"
    print("✅ Artifact Gap Verified: Mechanism correctly identifies missing physics.")