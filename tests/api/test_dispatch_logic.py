# tests/api/test_dispatch_logic.py

import pytest
import os
import uuid
import logging
from unittest.mock import patch, MagicMock
from src.api.github_trigger import Dispatcher

logger = logging.getLogger("Engine.Test.API")

# --- UNIT TESTS (MOCKED) ---

def test_dispatch_fails_without_token():
    """
    Rule 4 Compliance: Explicit error when GH_PAT is missing.
    Ensures the engine doesn't attempt a 'dead pulse'.
    """
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(RuntimeError, match="GH_PAT not found"):
            # The Dispatcher should check for the token during __init__
            Dispatcher()

@patch('requests.post')
def test_dispatch_signal_success(mock_post):
    """
    Verifies that a 204 No Content (Standard GitHub Success) 
    results in a successful internal boolean return.
    """
    # 1. Setup Mock Environment
    with patch.dict('os.environ', {'GH_PAT': 'mock_token_alpha_123'}):
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        # 2. Act
        dispatcher = Dispatcher()
        payload = {
            "step": "physics_solve", 
            "project_id": "OCEANS-V1",
            "manifest_id": "M-001"
        }
        
        success = dispatcher.trigger_worker("Dmitrii-Zavalin/worker-node", payload)
        
        # 3. Assert
        assert success is True
        # Verify the call was made with the correct Bearer token
        args, kwargs = mock_post.call_args
        assert "Authorization" in kwargs["headers"]
        assert "Bearer mock_token_alpha_123" in kwargs["headers"]["Authorization"]

@patch('requests.post')
def test_dispatch_signal_failure_handling(mock_post):
    """Verifies that non-204 status codes return False safely."""
    with patch.dict('os.environ', {'GH_PAT': 'mock_token'}):
        mock_response = MagicMock()
        mock_response.status_code = 401 # Unauthorized
        mock_post.return_value = mock_response
        
        dispatcher = Dispatcher()
        success = dispatcher.trigger_worker("org/repo", {"step": "test"})
        
        assert success is False

# --- PRODUCTION TEST (REAL-WORLD INTEGRATION) ---

def test_real_world_integration_handshake():
    """
    PRODUCTION TEST: End-to-End Handshake.
    Verifies the Engine can talk to a live worker repository.
    """
    # Skip if we aren't in a live environment (e.g. local dev without keys)
    if not os.getenv("GH_PAT"):
        pytest.skip("Skipping Real-World test: GH_PAT (GitHub PAT) not set in environment.")

    test_run_id = f"pulse_{uuid.uuid4().hex[:8]}"
    # Targeting your specific nomadic deployment repo
    target_repo = "Dmitrii-Zavalin-Deployments/navier_stokes_solver"
    
    payload = {
        "run_id": test_run_id,
        "step": "INTEGRATION_GATE",
        "input_file": "navier_stokes_params.json",
        "description": "Super-Rational Engine: Pre-Flight Integrity Pulse"
    }

    dispatcher = Dispatcher()
    
    try:
        success = dispatcher.trigger_worker(target_repo, payload)
        
        if not success:
            logger.warning("⚠️ Live Handshake Refused: Check GH_PAT scopes (must have 'workflow').")
            pytest.fail("GitHub API rejected the dispatch request.")
            
        assert success is True
        print(f"\n🚀 [SIGNAL SENT] Verify Run ID [{test_run_id}] in Actions for: {target_repo}")

    except Exception as e:
        pytest.fail(f"API Dispatch crashed with error: {e}")