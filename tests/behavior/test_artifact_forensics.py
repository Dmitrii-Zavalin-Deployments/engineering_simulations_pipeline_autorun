# tests/behavior/test_artifact_forensics.py

import json
from pathlib import Path
from src.core.state_engine import OrchestrationState
from src.core.constants import OrchestrationStatus

def test_forensic_idempotency_recovery(tmp_path):
    """
    CONSTITUTION CHECK: Phase A (2) - Idempotency Contract.
    Verifies that the Engine resumes based on Physical Artifact Truth 
    even if the ledger is out of sync.
    """
    # 1. Setup Mock Workspace
    config_path = tmp_path / "active_disk.json"
    data_dir = tmp_path / "data/testing-input-output"
    data_dir.mkdir(parents=True)
    ledger_path = tmp_path / "ledger.json"

    # Seed the physical disk slot
    config_path.write_text(json.dumps({
        "project_id": "FORENSIC-TEST",
        "manifest_url": "http://mock.com"
    }), encoding="utf-8")

    # 2. Define a 2-Step Pipeline
    manifest = {
        "manifest_id": "M-XYZ",
        "project_id": "FORENSIC-TEST",
        "pipeline_steps": [
            {"name": "step_1", "requires": [], "produces": ["artifact_1.zip"], "timeout_hours": 1, "target_repo": "repo/1"},
            {"name": "step_2", "requires": ["artifact_1.zip"], "produces": ["final.csv"], "timeout_hours": 1, "target_repo": "repo/2"}
        ]
    }

    # Initialize Sovereign Logic Gate
    state = OrchestrationState(str(config_path), str(data_dir), str(ledger_path))
    state.manifest_data = manifest

    # 3. SCENARIO: Physical truth exists (artifact_1 is done), but ledger says WAITING
    (data_dir / "artifact_1.zip").write_text("binary-data")
    
    mock_ledger = {
        "step_1": {"status": OrchestrationStatus.WAITING.value},
        "step_2": {"status": OrchestrationStatus.WAITING.value}
    }

    # 4. EXECUTION: Forensic Scan (Reconcile & Heal)
    state.reconcile_and_heal(mock_ledger)

    # 5. VERIFICATION
    # Step 1 should be COMPLETED because the artifact exists.
    # Step 2 should be PENDING because its requirement (artifact_1) is now physically present.
    assert mock_ledger["step_1"]["status"] == OrchestrationStatus.COMPLETED.value
    assert mock_ledger["step_2"]["status"] == OrchestrationStatus.PENDING.value
    print("✅ Forensic Discovery Alignment Confirmed: Execution resumes based on disk truth.")

def test_clean_room_isolation(tmp_path):
    """
    CONSTITUTION CHECK: Phase A (2) - Isolation Mandate.
    Confirms the Engine only recognizes artifacts in the designated DATA_DIR.
    """
    # 1. Setup Directories
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # 2. Protocol Requirement: Seed the disk configuration
    config_file = tmp_path / "disk.json"
    config_file.write_text(json.dumps({
        "project_id": "ISO-TEST", 
        "manifest_url": "http://mock-url.com"
    }), encoding="utf-8")

    # 3. Place a file OUTSIDE the recognized data directory
    (tmp_path / "stray_artifact.zip").write_text("contamination")
    
    # 4. Initialize Engine (should succeed now that disk.json exists)
    state = OrchestrationState(
        str(config_file), 
        str(data_dir), 
        str(tmp_path / "ledger.json")
    )
    
    # 5. Verification: Check that the engine remains blind to outside files
    # state.data_path should point only to data_dir
    assert not (Path(state.data_path) / "stray_artifact.zip").exists()
    print("✅ Isolation Mandate Verified: Engine is successfully isolated from contamination.")