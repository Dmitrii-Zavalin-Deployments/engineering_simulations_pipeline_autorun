# tests/test_dispatch_logic.py

import pytest
import logging
from unittest.mock import patch, MagicMock
from src.api.github_trigger import Dispatcher

# Standard logger setup for the test suite
logger = logging.getLogger(__name__)

@patch('requests.post')
def test_dispatch_signal_success(mock_post):
    """Verifies 204 status results in successful dispatch."""
    logger.info("Running: test_dispatch_signal_success")
    
    # Mock environment to satisfy Rule 4
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token_alpha'}):
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        dispatcher = Dispatcher()
        payload = {"step": "solve", "project_id": "test_project"}
        
        success = dispatcher.trigger_worker("org/repo", payload)
        
        assert success is True
        mock_post.assert_called_once()
        logger.debug("Successfully verified 204 dispatch signal.")

def test_dispatch_fails_without_token():
    """Rule 4 Compliance: Explicit error when GITHUB_TOKEN is missing."""
    logger.info("Running: test_dispatch_fails_without_token")
    
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(RuntimeError, match="GITHUB_TOKEN not found"):
            Dispatcher()
    
    logger.debug("Successfully caught missing GITHUB_TOKEN RuntimeError.")

@patch('requests.post')
def test_dispatch_api_rejection(mock_post):
    """Verifies that non-204 responses correctly return False."""
    logger.info("Running: test_dispatch_api_rejection")
    
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token_alpha'}):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        dispatcher = Dispatcher()
        success = dispatcher.trigger_worker("org/repo", {"step": "fail"})
        
        assert success is False
        logger.debug(f"Confirmed False return on {mock_response.status_code} status.")