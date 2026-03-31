# tests/test_integration_gate.py

import pytest
import json
from src.core.state_engine import OrchestrationState

def test_hard_halt_on_corrupt_manifest(tmp_path):
    """Rule Check: Verifies immediate Hard-Halt when manifest fails schema validation."""
    config = tmp_path / "active_disk.json"
    config.write_text(json.dumps({"project_id": "halt_test", "manifest_url": "http://x.com"}))
    
    # We must mock the schema path for the test environment
    state = OrchestrationState(str(config), str(tmp_path))
    
    # Missing required 'pipeline_steps' key - should trigger ValidationError
    corrupt_manifest = {"manifest_id": "bad_disk_v1"} 
    
    with pytest.raises(RuntimeError, match="Hard-Halt"):
        state.hydrate_manifest(corrupt_manifest)

def test_agnostic_execution_logic(tmp_path):
    """
    Zero-Physics Testing: Verify the engine doesn't care about file content,
    only existence (Horizontal Integrity Mandate).
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    config = tmp_path / "active_disk.json"
    config.write_text(json.dumps({"project_id": "physics_test", "manifest_url": "http://x.com"}))
    
    # Create 'Dummy' artifact (The engine is blind to content)
    (data_dir / "raw_input.txt").write_text("agnostic content")
    
    state = OrchestrationState(str(config), str(data_dir))
    valid_manifest = {
        "manifest_id": "v1",
        "pipeline_steps": [{
            "name": "calc_step",
            "target_repo": "org/worker",
            "requires": ["raw_input.txt"],
            "produces": ["output.csv"]
        }]
    }
    
    state.hydrate_manifest(valid_manifest)
    target = state.forensic_artifact_scan()
    
    assert target is not None
    assert target['name'] == "calc_step"