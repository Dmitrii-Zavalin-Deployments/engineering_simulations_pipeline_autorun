# tests/test_forensic_logic.py

import json
import pytest
from src.core.state_engine import OrchestrationState

def test_forensic_gap_detection(tmp_path):
    """Verifies engine triggers when output is missing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    config = tmp_path / "active_disk.json"
    config.write_text(json.dumps({"project_id": "test", "manifest_url": "http://x.com"}))

    # Create requirement file (The Evidence)
    (data_dir / "input.npy").write_text("data")

    state = OrchestrationState(str(config), str(data_dir))
    state.hydrate_manifest({
        "manifest_id": "v1",
        "pipeline_steps": [{
            "name": "solve",
            "target_repo": "org/repo",
            "requires": ["input.npy"],
            "produces": ["output.zip"]
        }]
    })

    step = state.forensic_artifact_scan()
    assert step is not None
    assert step['name'] == "solve"
    print("✅ Gap Detection Verified.")

def test_forensic_saturation(tmp_path):
    """Verifies engine stays idle when output exists."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    config = tmp_path / "active_disk.json"
    config.write_text(json.dumps({"project_id": "test", "manifest_url": "http://x.com"}))

    # Create both files (Pipeline is Saturated)
    (data_dir / "input.npy").write_text("x")
    (data_dir / "output.zip").write_text("y")

    state = OrchestrationState(str(config), str(data_dir))
    state.hydrate_manifest({
        "manifest_id": "v1",
        "pipeline_steps": [{
            "name": "solve", 
            "target_repo": "org/repo",
            "requires": ["input.npy"], 
            "produces": ["output.zip"]
        }]
    })

    assert state.forensic_artifact_scan() is None
    print("✅ Saturation Verified.")