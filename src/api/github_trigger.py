# src/api/github_trigger.py

import os
import logging
import requests
from typing import Dict, Any

# Configure Logger for Dispatch Traceability
# Note: Root logging config is typically handled in main_engine.py, 
# but local logger is defined for granular traceability.
logger = logging.getLogger("Engine.Dispatcher")

class Dispatcher:
    """
    The Command Link (Dispatch Protocol).
    Compliance: 
    - Rule 0: __slots__ Mandatory Architecture
    - Rule 3: Remote Dispatch Logic
    - Rule 4: Zero-Default Policy
    """
    
    # Rule 0: Mandatory __slots__ to eliminate dict overhead
    __slots__ = ['token', 'headers']

    def __init__(self):
        """
        Initializes the Dispatcher with explicit environment validation.
        Rule 4: Explicit or Error - No hardcoded fallback tokens.
        """
        # Phase C: Rule 4 - Zero-Default Policy (Explicit or Error)
        self.token = os.getenv("GH_PAT")  # Using the GH_PAT secret from your YAML
        
        if not self.token:
            logger.critical("GH_PAT not found in environment. Access Denied.")
            raise RuntimeError("❌ CRITICAL: GH_PAT not found. Dispatch aborted.")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def trigger_worker(self, target_repo: str, payload: Dict[str, Any]) -> bool:
        """
        Sends a Repository Dispatch signal to the nomadic worker.
        Rule 1: Isolation Mandate - Targets specific worker repos.
        """
        url = f"https://api.github.com/repos/{target_repo}/dispatches"
        
        # Dispatch Protocol: Event type 'worker_trigger' is expected by worker repos
        data = {
            "event_type": "worker_trigger",
            "client_payload": payload
        }

        # Rule 4 Violation Correction: Replaced .get() with direct access.
        # This ensures a Hard-Halt if the payload is malformed.
        try:
            step_name = payload['step'] 
            logger.info(f"📡 Dispatching Signal: [{target_repo}] for Step [{step_name}]")
        except KeyError:
            logger.critical("Dispatch Payload missing 'step' key. Protocol Breach.")
            raise KeyError("❌ CRITICAL: Step ID missing from dispatch payload.")

        try:
            # Phase C: Rule 1 - Resource Protection (Timeout enforced)
            # Rule 5: Operational Hygiene - 15s timeout prevents hanging runners
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