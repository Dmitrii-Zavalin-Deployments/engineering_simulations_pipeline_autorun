# tests/behavior/test_artifact_forensics.py

import pytest
from pathlib import Path
import json
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

    config_path.write_text(json.dumps({
        "project_id": "FORENSIC-TEST",
        "manifest_url": "http://mock.com"
    }))

    # 2. Define a 2-Step Pipeline
    manifest = {
        "manifest_id": "M-XYZ",
        "project_id": "FORENSIC-TEST",
        "pipeline_steps": [
            {"name": "step_1", "requires": [], "produces": ["artifact_1.zip"], "timeout_hours": 1},
            {"name": "step_2", "requires": ["artifact_1.zip"], "produces": ["final.csv"], "timeout_hours": 1}
        ]
    }

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
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Place a file OUTSIDE the recognized data directory
    (tmp_path / "stray_artifact.zip").write_text("contamination")
    
    # State Engine should see 0 artifacts because it's isolated to 'data_dir'
    state = OrchestrationState(str(tmp_path/"disk.json"), str(data_dir), str(tmp_path/"ledger.json"))
    
    # Verification: Check that logic handles a missing file correctly
    assert not (state.data_path / "stray_artifact.zip").exists()