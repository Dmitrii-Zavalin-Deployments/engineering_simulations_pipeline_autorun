# tests/test_forensic_logic.py

import json
from src.core.state_engine import OrchestrationState

def test_idempotency_logic_gap_detection(tmp_path):
    """
    Verifies that the engine detects a gap when input exists but output is missing.
    Phase C Compliance: Rule 3 - Data Integrity.
    """
    # 1. Setup the Infrastructure Sink
    config_file = tmp_path / "active_disk.json"
    config_file.write_text(json.dumps({
        "project_id": "test_project_alpha",
        "manifest_url": "https://raw.githubusercontent.com/test/manifest.json"
    }))
    
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # 2. Create the Artifact Signal (The Evidence)
    (data_dir / "geometry.msh").write_text("dummy mesh data")

    # 3. Initialize Engine & Hydrate with a Compliant Manifest
    state = OrchestrationState(str(config_file), str(data_dir))
    state.hydrate_manifest({
        "manifest_id": "test_manifest_v1",  # REQUIRED: Phase C, Rule 4
        "pipeline_steps": [
            {
                "name": "solver",
                "target_repo": "test/solver-repo",
                "requires": ["geometry.msh"],
                "produces": ["results.zip"]
            }
        ]
    })

    # 4. Execute Forensic Scan
    step = state.forensic_artifact_scan()
    
    assert step is not None
    assert step['name'] == "solver"
    print("✅ Gap Detection Verified: Engine triggered on missing output.")

def test_idempotency_logic_saturation(tmp_path):
    """
    Verifies the engine stays idle if the output already exists.
    Phase C Compliance: Rule 3 - Deterministic Idempotency.
    """
    config_file = tmp_path / "active_disk.json"
    config_file.write_text(json.dumps({"project_id": "test", "manifest_url": "x"}))
    
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create BOTH input and output (Pipeline is Saturated)
    (data_dir / "geometry.msh").write_text("x")
    (data_dir / "results.zip").write_text("y")

    state = OrchestrationState(str(config_file), str(data_dir))
    state.hydrate_manifest({
        "manifest_id": "test_manifest_v1",
        "pipeline_steps": [
            {
                "name": "solver", 
                "target_repo": "test/solver-repo",
                "requires": ["geometry.msh"], 
                "produces": ["results.zip"]
            }
        ]
    })

    # Execute Scan: Should return None
    assert state.forensic_artifact_scan() is None
    print("✅ Saturation Verified: Engine remained idle as expected.")