# tests/behavior/test_forensic_logic.py

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Assuming core classes are accessible
from src.core.state_engine import StateEngine, OrchestrationState

@pytest.fixture
def mock_env(tmp_path):
    """Sets up a nomadic environment with a /data folder and a ledger."""
    project_root = tmp_path / "nomadic_root"
    project_root.mkdir()
    data_dir = project_root / "data"
    data_dir.mkdir()
    
    ledger_file = project_root / "orchestration_ledger.json"
    
    # Define a standard 2-step pipeline for testing
    manifest = {
        "project_id": "behavioral-test-suite",
        "pipeline_steps": [
            {
                "step_name": "generate_mesh",
                "target_repo": "mesh-worker",
                "timeout_hours": 2,
                "inputs": [],
                "outputs": ["geometry.msh"]
            },
            {
                "step_name": "run_physics",
                "target_repo": "physics-worker",
                "timeout_hours": 6,
                "inputs": ["geometry.msh"],
                "outputs": ["results.zip"]
            }
        ]
    }
    
    return {
        "root": project_root,
        "data": data_dir,
        "ledger": ledger_file,
        "manifest": manifest
    }

def test_scenario_gap_detected(mock_env):
    """
    Scenario: Gap Detected
    Physical: Data folder is empty.
    Ledger: Empty.
    Expectation: Dispatch first step (mesh).
    """
    engine = StateEngine(root_path=mock_env["root"], manifest=mock_env["manifest"])
    decision = engine.analyze_state()
    
    assert decision["action"] == "DISPATCH"
    assert decision["step_name"] == "generate_mesh"

def test_scenario_in_flight_lock(mock_env):
    """
    Scenario: In-Flight Lock
    Physical: Inputs present, Outputs missing.
    Ledger: Status is IN_PROGRESS and time is within limits.
    Expectation: Skip (Wait for worker).
    """
    # 1. Setup physical state (inputs for step 2 exist, but not outputs)
    (mock_env["data"] / "geometry.msh").write_text("dummy mesh data")
    
    # 2. Setup ledger state (Step 2 was triggered 30 mins ago)
    recent_time = (datetime.now() - timedelta(minutes=30)).isoformat()
    mock_env["ledger"].write_text(json.dumps({
        "run_physics": {
            "status": "IN_PROGRESS",
            "last_triggered": recent_time
        }
    }))
    
    engine = StateEngine(root_path=mock_env["root"], manifest=mock_env["manifest"])
    decision = engine.analyze_state()
    
    # Logic: Even though output results.zip is missing, the lock is valid.
    assert decision["action"] == "SKIP"
    assert decision["reason"] == "WORKER_ACTIVE"

def test_scenario_timeout_recovery(mock_env):
    """
    Scenario: Timeout Recovery (Rule 4 Enforcement)
    Physical: Inputs present, Outputs missing.
    Ledger: IN_PROGRESS but time > timeout_hours (2h for mesh).
    Expectation: Re-Dispatch (Stale lock broken).
    """
    # 1. Setup physical state (Outputs for mesh missing)
    # 2. Setup ledger state (Mesh triggered 5 hours ago, timeout is 2h)
    stale_time = (datetime.now() - timedelta(hours=5)).isoformat()
    mock_env["ledger"].write_text(json.dumps({
        "generate_mesh": {
            "status": "IN_PROGRESS",
            "last_triggered": stale_time
        }
    }))
    
    engine = StateEngine(root_path=mock_env["root"], manifest=mock_env["manifest"])
    decision = engine.analyze_state()
    
    # Logic: Lock is stale. Break it and re-dispatch.
    assert decision["action"] == "RE_DISPATCH"
    assert decision["step_name"] == "generate_mesh"
    assert "STALE_LOCK_BROKEN" in decision["audit_note"]

def test_scenario_saturated_step(mock_env):
    """
    Scenario: Saturated Step (Cycle Complete)
    Physical: Inputs and Outputs for step exist.
    Expectation: Clear Lock and move to next or Halt.
    """
    # Physical state: All files for step 1 exist
    (mock_env["data"] / "geometry.msh").write_text("exists")
    
    # Ledger says it's still in progress
    mock_env["ledger"].write_text(json.dumps({
        "generate_mesh": {"status": "IN_PROGRESS"}
    }))
    
    engine = StateEngine(root_path=mock_env["root"], manifest=mock_env["manifest"])
    decision = engine.analyze_state()
    
    # Logic: Output exists! Update ledger to COMPLETED and look for next gap.
    assert decision["updated_status"] == "COMPLETED"
    # It should then identify that step 2 is the next gap
    assert decision["next_action"] == "DISPATCH"
    assert decision["next_step"] == "run_physics"

def test_scenario_blocked_step(mock_env):
    """
    Scenario: Blocked Step
    Physical: Inputs for step 2 are MISSING.
    Expectation: Skip (Dependencies not met).
    """
    # Physical: data/ is empty (no geometry.msh for step 2)
    # Manifest says step 1 is done or we skip to step 2 check
    engine = StateEngine(root_path=mock_env["root"], manifest=mock_env["manifest"])
    
    # We force the engine to evaluate step 2
    decision = engine.evaluate_step(mock_env["manifest"]["pipeline_steps"][1])
    
    assert decision["action"] == "SKIP"
    assert decision["reason"] == "MISSING_INPUTS"