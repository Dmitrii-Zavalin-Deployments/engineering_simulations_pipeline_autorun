# tests/behavior/test_forensic_logic.py

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# SSoT: Aligned with your verified physical file and class name
from src.core.state_engine import OrchestrationState

@pytest.fixture
def mock_env(tmp_path):
    """Sets up a nomadic environment with a /data folder and a ledger."""
    # SSoT: Project structure alignment to mirror real execution
    project_root = tmp_path / "artifact_driven_simulation_engine"
    project_root.mkdir()
    
    # Matching the engine's artifact discovery path
    data_dir = project_root / "data" / "testing-input-output"
    data_dir.mkdir(parents=True)
    
    config_dir = project_root / "config"
    config_dir.mkdir()
    
    # Create a dummy schema for validation compliance check in OrchestrationState
    schema_path = config_dir / "core_schema.json"
    schema_path.write_text(json.dumps({
        "type": "object",
        "properties": {
            "manifest_id": {"type": "string"},
            "pipeline_steps": {"type": "array"}
        },
        "required": ["manifest_id", "pipeline_steps"]
    }))

    # Define the active_disk.json (Core Config)
    config_path = config_dir / "active_disk.json"
    config_path.write_text(json.dumps({
        "project_id": "behavioral-test-suite",
        "manifest_url": "http://localhost/manifest.json"
    }))
    
    # Define the Manifest (Hydration Data) with your actual logic keys
    manifest = {
        "manifest_id": "M-UNIT-TEST-001",
        "pipeline_steps": [
            {
                "name": "generate_mesh",
                "target_repo": "mesh-worker",
                "timeout_hours": 2,
                "requires": [],
                "produces": ["geometry.msh"]
            },
            {
                "name": "run_physics",
                "target_repo": "physics-worker",
                "timeout_hours": 6,
                "requires": ["geometry.msh"],
                "produces": ["results.zip"]
            }
        ]
    }
    
    return {
        "root": project_root,
        "config": str(config_path),
        "data": str(data_dir),
        "manifest": manifest
    }

def test_scenario_gap_detected(mock_env):
    """
    Scenario: Gap Detected
    Physical: Data folder is empty. Ledger: Empty.
    Expectation: forensic_artifact_scan identifies 'generate_mesh'.
    """
    # Initialize with schema check mock
    with patch("src.core.state_engine.Path.exists", return_value=True):
        engine = OrchestrationState(mock_env["config"], mock_env["data"])
        engine.hydrate_manifest(mock_env["manifest"])
    
    orchestration_ledger = {}
    ready_steps = engine.forensic_artifact_scan(orchestration_ledger)
    
    assert ready_steps is not None
    assert ready_steps[0]["name"] == "generate_mesh"

def test_scenario_in_flight_lock(mock_env):
    """
    Scenario: In-Flight Lock
    Physical: Inputs present, Outputs missing.
    Ledger: Status is IN_PROGRESS and time is within limits.
    Expectation: Skip (Worker active).
    """
    # 1. Setup physical state (inputs for step 2 exist)
    Path(mock_env["data"], "geometry.msh").write_text("dummy mesh")
    
    engine = OrchestrationState(mock_env["config"], mock_env["data"])
    engine.hydrate_manifest(mock_env["manifest"])
    
    # 2. Setup ledger state (Step 2 triggered recently)
    recent_time = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    orchestration_ledger = {
        "run_physics": {
            "status": "IN_PROGRESS",
            "last_triggered": recent_time,
            "timeout_hours": 6
        }
    }
    
    ready_steps = engine.forensic_artifact_scan(orchestration_ledger)
    
    # Logic: forensic_artifact_scan filters out 'In-Flight' locks that haven't timed out
    assert ready_steps is None

def test_scenario_timeout_recovery(mock_env):
    """
    Scenario: Timeout Recovery (Rule 4 Enforcement)
    Physical: Inputs present, Outputs missing.
    Ledger: IN_PROGRESS but time > timeout_hours.
    Expectation: Re-identify for Dispatch (Stale lock broken).
    """
    engine = OrchestrationState(mock_env["config"], mock_env["data"])
    engine.hydrate_manifest(mock_env["manifest"])
    
    # Mesh triggered 5 hours ago (Timeout is 2h)
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    orchestration_ledger = {
        "generate_mesh": {
            "status": "IN_PROGRESS",
            "last_triggered": stale_time,
            "timeout_hours": 2
        }
    }
    
    ready_steps = engine.forensic_artifact_scan(orchestration_ledger)
    
    # Logic: Lock is stale, so the step is returned as ready for re-dispatch
    assert ready_steps is not None
    assert ready_steps[0]["name"] == "generate_mesh"

def test_scenario_saturated_state(mock_env):
    """
    Scenario: Saturated State (Cycle Complete)
    Physical: All expected artifacts exist on disk.
    Expectation: Return None (Mission Complete).
    """
    # Physical state: All files exist
    Path(mock_env["data"], "geometry.msh").write_text("exists")
    Path(mock_env["data"], "results.zip").write_text("exists")
    
    engine = OrchestrationState(mock_env["config"], mock_env["data"])
    engine.hydrate_manifest(mock_env["manifest"])
    
    orchestration_ledger = {}
    ready_steps = engine.forensic_artifact_scan(orchestration_ledger)
    
    # Logic: If artifacts exist, the step is not "Ready" for work
    assert ready_steps is None

def test_scenario_blocked_step(mock_env):
    """
    Scenario: Blocked Step
    Physical: Inputs for step 2 (run_physics) are MISSING.
    Expectation: Step 2 is not returned even if step 1 is done.
    """
    engine = OrchestrationState(mock_env["config"], mock_env["data"])
    engine.hydrate_manifest(mock_env["manifest"])
    
    # Ledger shows step 1 is done
    orchestration_ledger = {
        "generate_mesh": {"status": "COMPLETED"}
    }
    
    # BUT, physical artifact 'geometry.msh' is missing from disk
    ready_steps = engine.forensic_artifact_scan(orchestration_ledger)
    
    # Logic: Artifact presence is the primary truth. No mesh = No physics.
    assert ready_steps is None