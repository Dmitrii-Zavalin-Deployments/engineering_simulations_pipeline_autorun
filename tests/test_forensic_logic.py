# tests/test_forensic_logic.py

import pytest
import json
from src.core.state_engine import OrchestrationState

def test_idempotency_logic_gap_detection(tmp_path):
    """Verifies that the engine detects a gap when input exists but output is missing."""
    # Setup test environment
    config_file = tmp_path / "active_disk.json"
    config_file.write_text(json.dumps({
        "project_id": "test",
        "manifest_url": "http://example.com"
    }))
    
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create the requirement (The Evidence)
    (data_dir / "geometry.msh").write_text("dummy mesh")

    # Initialize Engine
    state = OrchestrationState(str(config_file), str(data_dir))
    state.hydrate_manifest({
        "pipeline_steps": [
            {
                "name": "solver",
                "requires": ["geometry.msh"],
                "produces": ["results.zip"]
            }
        ]
    })

    # Execute Scan
    step = state.forensic_artifact_scan()
    
    assert step is not None
    assert step['name'] == "solver"

def test_idempotency_logic_saturation(tmp_path):
    """Verifies the engine stays idle if the output already exists."""
    config_file = tmp_path / "active_disk.json"
    config_file.write_text(json.dumps({"project_id": "test", "manifest_url": "x"}))
    
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "geometry.msh").write_text("x")
    (data_dir / "results.zip").write_text("y") # The evidence of completion

    state = OrchestrationState(str(config_file), str(data_dir))
    state.hydrate_manifest({
        "pipeline_steps": [{"name": "s", "requires": ["geometry.msh"], "produces": ["results.zip"]}]
    })

    assert state.forensic_artifact_scan() is None