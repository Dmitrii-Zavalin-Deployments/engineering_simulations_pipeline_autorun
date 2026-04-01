# src/api/github_trigger.py

import os
import logging
import requests
from typing import Dict, Any

# Configure Logger for Dispatch Traceability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("Engine.Dispatcher")

class Dispatcher:
    """
    The Command Link (Dispatch Protocol).
    Phase C Compliance: Rule 0 (__slots__) & Rule 3 (Remote Execution).
    """
    __slots__ = ['token', 'headers']

    def __init__(self):
        # Phase C: Rule 4 - Zero-Default Policy (Explicit or Error)
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            logger.critical("GITHUB_TOKEN not found in environment. Access Denied.")
            raise RuntimeError("❌ CRITICAL: GITHUB_TOKEN not found. Dispatch aborted.")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def trigger_worker(self, target_repo: str, payload: Dict[str, Any]) -> bool:
        """
        Sends a Repository Dispatch signal to the worker.
        Target: https://api.github.com/repos/{target_repo}/dispatches
        """
        url = f"https://api.github.com/repos/{target_repo}/dispatches"
        
        # Dispatch Protocol: Event type 'worker_trigger' is expected by worker repos
        data = {
            "event_type": "worker_trigger",
            "client_payload": payload
        }

        step_name = payload.get('step', 'UNKNOWN_STEP')
        logger.info(f"📡 Dispatching Signal: [{target_repo}] for Step [{step_name}]")

        try:
            # Phase C: Rule 1 - Resource Protection (Timeout enforced)
            response = requests.post(url, json=data, headers=self.headers, timeout=15)
            
            # GitHub returns 204 No Content on successful dispatch
            if response.status_code == 204:
                logger.info(f"🚀 Signal Accepted: {target_repo} activation confirmed.")
                return True
            
            logger.error(f"❌ Handshake Refused: HTTP {response.status_code} - {response.text}")
            return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Connection Error during Dispatch to {target_repo}: {e}")
            return False