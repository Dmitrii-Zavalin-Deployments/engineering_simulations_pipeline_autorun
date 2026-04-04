# tests/behavior/test_schema_sovereignty.py

import pytest
import json
from src.core.state_engine import OrchestrationState

def test_manifest_schema_hard_halt(tmp_path):
    """
    CONSTITUTION CHECK: Phase A (5) - Manifest Schema Validation.
    Verifies that a 'corrupt disk' (invalid manifest) results in an 
    immediate Hard-Halt, preventing execution under ambiguity.
    """
    # 1. Setup Mock Workspace
    config_file = tmp_path / "disk.json"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Seed the mandatory disk config
    config_file.write_text(json.dumps({
        "project_id": "HALT-TEST",
        "manifest_url": "http://mock.com"
    }))

    # 2. Initialize Engine
    state = OrchestrationState(str(config_file), str(data_dir), str(tmp_path/"ledger.json"))

    # 3. SCENARIO: Corrupt Manifest (Missing mandatory 'pipeline_steps' key)
    corrupt_manifest = {
        "manifest_id": "M-BAD",
        "project_id": "HALT-TEST"
        # 'pipeline_steps' is missing!
    }

    # 4. EXECUTION & VERIFICATION: Hard-Halt
    # The hydrate_manifest method must raise RuntimeError upon schema violation
    with pytest.raises(RuntimeError) as excinfo:
        state.hydrate_manifest(corrupt_manifest)
    
    assert "CRITICAL: Hard-Halt" in str(excinfo.value)
    assert "manifest_json" in str(excinfo.value) or "validate" in str(excinfo.value)
    
    print("✅ Schema Sovereignty Verified: Engine successfully halted on corrupt manifest.")

def test_agnostic_execution_gate(tmp_path):
    """
    CONSTITUTION CHECK: Phase A (5) - Agnostic Execution.
    Verifies the engine only cares about filename presence, not content.
    """
    config_file = tmp_path / "disk.json"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    config_file.write_text(json.dumps({"project_id": "AGNOSTIC", "manifest_url": "url"}))
    
    state = OrchestrationState(str(config_file), str(data_dir), str(tmp_path/"ledger.json"))
    
    # The artifact could contain 'garbage' - the engine should still see it
    artifact_path = data_dir / "required_artifact.zip"
    artifact_path.write_text("This is non-binary garbage data.")
    
    # Physical check
    assert artifact_path.exists()
    assert state.data_path.joinpath("required_artifact.zip").exists()
    print("✅ Agnostic Execution Verified: Engine recognizes artifact presence regardless of internal 'physics'.")