# tests/behavior/test_forensic_behavior.py

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from src.core.state_engine import OrchestrationState

@pytest.fixture
def mock_env(tmp_path):
    """Sets up environment for Edge Case testing."""
    project_root = tmp_path / "simulation_engine"
    project_root.mkdir()
    data_dir = project_root / "data"
    data_dir.mkdir()
    config_dir = project_root / "config"
    config_dir.mkdir()
    
    (config_dir / "core_schema.json").write_text(json.dumps({"type": "object"}))
    config_path = config_dir / "active_disk.json"
    config_path.write_text(json.dumps({"project_id": "behavior-test", "manifest_url": "http://io"}))
    
    manifest = {
        "manifest_id": "M-BEHAVIOR-001",
        "pipeline_steps": [
            {"name": "step_1", "target_repo": "r1", "timeout_hours": 2, "requires": [], "produces": ["f1.out"]},
            {"name": "step_2", "target_repo": "r2", "timeout_hours": 6, "requires": ["f1.out"], "produces": ["f2.out"]}
        ]
    }
    
    return {"config": str(config_path), "data": str(data_dir), "manifest": manifest}

def test_scenario_in_flight_lock(mock_env):
    """Scenario: Verify valid IN_PROGRESS status prevents re-dispatch."""
    with patch("src.core.state_engine.Path.exists", return_value=True):
        engine = OrchestrationState(mock_env["config"], mock_env["data"])
        engine.hydrate_manifest(mock_env["manifest"])
    
    # Inputs for step 2 are there, but step 2 is currently running (not timed out)
    Path(mock_env["data"], "f1.out").write_text("data")
    recent_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    ledger = {"step_2": {"status": "IN_PROGRESS", "last_triggered": recent_time, "timeout_hours": 6}}
    
    assert engine.forensic_artifact_scan(ledger) is None

def test_scenario_timeout_recovery(mock_env):
    """Scenario: Verify stale IN_PROGRESS status triggers recovery."""
    with patch("src.core.state_engine.Path.exists", return_value=True):
        engine = OrchestrationState(mock_env["config"], mock_env["data"])
        engine.hydrate_manifest(mock_env["manifest"])
    
    # Step 1 running for 5 hours (Timeout is 2)
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    ledger = {"step_1": {"status": "IN_PROGRESS", "last_triggered": stale_time, "timeout_hours": 2}}
    
    ready = engine.forensic_artifact_scan(ledger)
    assert ready[0]["name"] == "step_1"

def test_scenario_blocked_step(mock_env):
    """Scenario: Verify ledger 'COMPLETED' is ignored if file is missing physically."""
    with patch("src.core.state_engine.Path.exists", return_value=True):
        engine = OrchestrationState(mock_env["config"], mock_env["data"])
        engine.hydrate_manifest(mock_env["manifest"])
    
    ledger = {"step_1": {"status": "COMPLETED"}}
    # f1.out is MISSING physically -> step_2 cannot run
    assert engine.forensic_artifact_scan(ledger) is None