# tests/core/test_future_proof.py

import pytest
import json
from src.core.state_engine import OrchestrationState

@pytest.fixture
def future_engine_setup(tmp_path):
    """Sets up an Agnostic Engine instance with a future-project manifest."""
    config = tmp_path / "active_disk.json"
    config.write_text(json.dumps({
        "project_id": "future_project_x", 
        "manifest_url": "http://nomadic-storage.io/x.json"
    }))
    
    # Mock Schema for compliance
    schema_dir = tmp_path / "config"
    schema_dir.mkdir()
    (schema_dir / "core_schema.json").write_text(json.dumps({"type": "object"}))
    
    # The 'Dummy Disc' Manifest
    future_manifest = {
        "manifest_id": "v99_experimental",
        "pipeline_steps": [
            {
                "name": "quantum_init",
                "requires": ["initial_seed.dat"],
                "produces": ["quantum_state.bin"],
                "target_repo": "org/quantum-worker"
            }
        ]
    }
    
    data_dir = tmp_path / "data"
    state = OrchestrationState(str(config), str(data_dir))
    state.schema_path = schema_dir / "core_schema.json"
    state.hydrate_manifest(future_manifest)
    return state

def test_dummy_disc_agnostic_execution(future_engine_setup):
    """
    SCENARIO 1: The 'Dummy Disc' Test.
    The Engine must process 'future_project_x' without any specific 
    knowledge of the physics or domain.
    """
    # 1. Provide the requirement for the future step
    (future_engine_setup.data_path / "initial_seed.dat").write_text("010101")
    
    # 2. Trigger Scan
    steps = future_engine_setup.forensic_artifact_scan({})
    step = steps[0] if steps else None
    
    # 3. Verify the Engine identified the future step based on Logic alone
    assert step['name'] == "quantum_init"
    assert step['target_repo'] == "org/quantum-worker"
    print("\n✅ Agnostic Execution Verified: Future Project X correctly identified.")

def test_conflict_simulation_hard_halt(future_engine_setup):
    """
    SCENARIO 2: Conflict Simulation (Broken Sync).
    If a file is missing due to a Dropbox sync failure, the Engine
    must return None (Halt) rather than moving forward.
    """
    # 1. Ensure the directory is empty (Simulating a sync that never happened)
    # No 'initial_seed.dat' exists.
    
    # 2. Trigger Scan
    steps = future_engine_setup.forensic_artifact_scan({})
    step = steps[0] if steps else None
    
    # 3. Verify Hard-Halt (No step should be triggered)
    assert step is None
    print("\n✅ Hard-Halt Verified: Engine refused to proceed with missing artifacts.")