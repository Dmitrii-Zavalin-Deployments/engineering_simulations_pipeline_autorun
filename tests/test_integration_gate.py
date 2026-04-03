# tests/test_integration_gate.py

import pytest
import json
import os
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path

# Internal Core Imports
from src.core.state_engine import OrchestrationState
from src.api.github_trigger import Dispatcher
from src.core.constants import OrchestrationStatus, SystemPaths
from tests.helpers.state_engine_dummy import StateEngineDummy

logger = logging.getLogger("Engine.Test.Integration")

## ==========================================================
## TIER 1: THE "CORRUPT DISC" GATE (Validation Integrity)
## ==========================================================

def test_system_tier_schema_enforcement(tmp_path):
    """
    VERIFICATION: Sovereign Schema Enforcement.
    The Engine must Hard-Halt if the manifest violates the local JSON schema.
    This prevents the nomadic node from executing a 'Damaged Disc'.
    """
    # 1. Setup physical env with dummy factory
    state, data_path = StateEngineDummy.create(tmp_path)
    
    # 2. Poison the manifest: missing 'manifest_id' and 'pipeline_steps'
    invalid_manifest = {
        "project_id": "P-001",
        "random_noise": "invalid_data"
    }
    
    # 3. Assert Hard-Halt (Rule 4 Compliance)
    with pytest.raises(RuntimeError, match="Hard-Halt"):
        state.hydrate_manifest(invalid_manifest)


## ==========================================================
## TIER 2: THE "FORENSIC GAP" GATE (Zero-Physics Logic)
## ==========================================================

def test_system_tier_gap_resolution(tmp_path):
    """
    VERIFICATION: Physics-Agnostic Gap Detection.
    Verifies the engine identifies the artifact gap based on existence alone.
    """
    # 1. Setup 1-step pipeline
    steps = [{
        "name": "ProcessData",
        "target_repo": "org/processor-worker",
        "requires": ["input_sensor.bin"],
        "produces": ["output_report.pdf"],
        "timeout_hours": 1
    }]
    state, data_path = StateEngineDummy.create(tmp_path, steps=steps)
    
    # 2. Arrange: Input exists, Output does NOT
    (data_path / "input_sensor.bin").write_text("DUMMY_BINARY", encoding="utf-8") 
    
    # 3. Act: Run the Forensic Loop
    healed = state.reconcile_and_heal({})
    ready = state.get_ready_steps(healed)
    
    # 4. Assert: Engine identifies the gap correctly
    assert ready is not None
    assert ready[0]['name'] == "ProcessData"
    assert "input_sensor.bin" in ready[0]['requires']
    assert healed["ProcessData"]["status"] == OrchestrationStatus.PENDING.value


## ==========================================================
## TIER 3: THE "DISPATCH COMMAND" GATE (Sovereign Authority)
## ==========================================================

@patch('src.api.github_trigger.requests.post')
def test_system_tier_dispatch_mechanism(mock_post):
    """
    VERIFICATION: Authorized Signal Transmission.
    Ensures the Dispatcher correctly formats the payload for the nomadic worker nodes.
    """
    # 1. Setup Mock Environment (Rule 4: Token must exist)
    with patch.dict('os.environ', {'GH_PAT': 'nomadic_test_token'}):
        # 2. Mock GitHub 204 Success Response
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        # 3. Execute Dispatcher Authority
        dispatcher = Dispatcher()
        payload = {"step": "AnalyzeWeather", "project": "P-001"}
        success = dispatcher.trigger_worker("Dmitrii-Zavalin/weather-worker", payload)
        
        # 4. Assertions
        assert success is True
        mock_post.assert_called_once()
        
        # Verify API logic
        args, kwargs = mock_post.call_args
        assert "Dmitrii-Zavalin/weather-worker" in args[0]
        # Verify the "Super-Rational" payload structure
        assert kwargs['json']['event_type'] == "worker_trigger"
        assert kwargs['json']['client_payload']['step'] == "AnalyzeWeather"


## ==========================================================
## TIER 4: THE "IDEMPOTENCY" GATE (Silent Operator)
## ==========================================================

def test_system_tier_saturation_silence(tmp_path):
    """
    VERIFICATION: Silent Operator Rule.
    If all artifacts exist, the Engine must remain silent (Zero Redundancy).
    """
    # 1. Setup 1-step pipeline
    steps = [{
        "name": "StepOne",
        "target_repo": "org/worker",
        "requires": ["input.txt"],
        "produces": ["output.csv"],
        "timeout_hours": 1
    }]
    state, data_path = StateEngineDummy.create(tmp_path, steps=steps)
    
    # 2. Arrange: Saturated State (Both Input and Output exist)
    (data_path / "input.txt").write_text("data", encoding="utf-8")
    (data_path / "output.csv").write_text("results", encoding="utf-8")
    
    # 3. Act: Scan the vault
    healed = state.reconcile_and_heal({})
    ready = state.get_ready_steps(healed)
    
    # 4. Assert: Zero gaps, status is COMPLETED
    assert ready is None
    assert healed["StepOne"]["status"] == OrchestrationStatus.COMPLETED.value
    logger.info("✅ Saturation Silence Verified: No redundant tasks triggered.")