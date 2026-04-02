# tests/test_integration_gate.py

import pytest
import json
import os
import logging
from unittest.mock import patch, MagicMock
from src.core.state_engine import OrchestrationState
from src.api.github_trigger import Dispatcher

# Ensure logger is visible during test output if needed
logger = logging.getLogger("Engine.Test")

## ==========================================================
## TIER 1: THE "CORRUPT DISC" GATE (Validation Integrity)
## ==========================================================

def test_system_tier_schema_enforcement(tmp_path):
    """
    VERIFICATION: Engine must Hard-Halt if the manifest violates the Sovereign Schema.
    This guarantees that the 'Console' won't attempt to play a 'Damaged Disc'.
    """
    # 1. Setup temporary environment
    config = tmp_path / "active_disk.json"
    config.write_text(json.dumps({"project_id": "P-001", "manifest_url": "http://mock.io/v1"}))
    
    # 2. Create an invalid manifest (missing required 'pipeline_steps' per core_schema.json)
    invalid_manifest = {"manifest_id": "M-999", "project_id": "P-001"}
    
    state = OrchestrationState(str(config), str(tmp_path))
    
    # 3. Assert Hard-Halt logic
    with pytest.raises(RuntimeError, match="Hard-Halt"):
        state.hydrate_manifest(invalid_manifest)


## ==========================================================
## TIER 2: THE "FORENSIC GAP" GATE (Zero-Physics Logic)
## ==========================================================

def test_system_tier_gap_resolution(tmp_path):
    """
    VERIFICATION: Engine identifies the exact artifact gap based on existence.
    Checks the 'Horizontal Integrity Mandate'—it is blind to file content.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # 1. Simulate 'Physics-Agnostic' presence: Input exists, Output does not.
    (data_dir / "input_sensor.bin").write_text("dummy_binary_data") 
    
    # 2. Valid Manifest defining the Gate
    manifest = {
        "manifest_id": "M-001",
        "pipeline_steps": [{
            "name": "ProcessData",
            "target_repo": "org/processor-worker",
            "requires": ["input_sensor.bin"],
            "produces": ["output_report.pdf"]
        }]
    }
    
    config = tmp_path / "active_disk.json"
    config.write_text(json.dumps({"project_id": "P-001", "manifest_url": "http://mock.io"}))
    
    state = OrchestrationState(str(config), str(data_dir))
    state.hydrate_manifest(manifest)
    
    # 3. Verify Mechanism identifies the gap
    gaps = state.forensic_artifact_scan({})
    gap = gaps[0] if gaps else None
    assert gap is not None
    assert gap['name'] == "ProcessData"
    assert "input_sensor.bin" in gap['requires']


## ==========================================================
## TIER 3: THE "DISPATCH COMMAND" GATE (Sovereign Authority)
## ==========================================================

@patch('src.api.github_trigger.requests.post')
def test_system_tier_dispatch_mechanism(mock_post):
    """
    VERIFICATION: Sovereign Logic - Verifies the signal is sent correctly to GitHub.
    Ensures the Dispatcher correctly formats the payload for the remote Repo.
    """
    # 1. Setup Mock Environment
    os.environ["GH_PAT"] = "nomadic_test_token"
    
    # 2. Setup Success Response (HTTP 204 No Content is standard for GitHub Dispatches)
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_post.return_value = mock_response
    
    # 3. Execute Dispatcher Mechanism
    dispatcher = Dispatcher()
    payload = {"step": "AnalyzeWeather", "project": "P-001"}
    success = dispatcher.trigger_worker("org/weather-worker", payload)
    
    # 4. Assertions
    assert success is True
    mock_post.assert_called_once()
    
    # Verify the logic correctly addressed the Repo Dispatch API
    args, kwargs = mock_post.call_args
    assert "org/weather-worker" in args[0]
    assert kwargs['json']['event_type'] == "worker_trigger"
    assert kwargs['json']['client_payload']['step'] == "AnalyzeWeather"


## ==========================================================
## TIER 4: THE "IDEMPOTENCY" GATE (Silent Operator)
## ==========================================================

def test_system_tier_saturation_silence(tmp_path):
    """
    VERIFICATION: If all artifacts exist, the Engine must remain silent and halt.
    Prevents redundant execution (The 'Silent Operator' Rule).
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # 1. Simulate a Saturated State (Both Input and Output exist)
    (data_dir / "input.txt").write_text("data")
    (data_dir / "output.csv").write_text("results")
    
    manifest = {
        "manifest_id": "M-Complete",
        "pipeline_steps": [{
            "name": "StepOne",
            "target_repo": "org/worker",
            "requires": ["input.txt"],
            "produces": ["output.csv"]
        }]
    }
    
    config = tmp_path / "active_disk.json"
    config.write_text(json.dumps({"project_id": "P-FULL", "manifest_url": "http://mock.io"}))
    
    state = OrchestrationState(str(config), str(data_dir))
    state.hydrate_manifest(manifest)
    
    # 2. Scan should return None (No gaps)
    gaps = state.forensic_artifact_scan({})
    gap = gaps[0] if gaps else None
    assert gap is None