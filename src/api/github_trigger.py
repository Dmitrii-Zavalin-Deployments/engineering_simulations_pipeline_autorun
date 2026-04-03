import os
import logging
import requests
from typing import Dict, Any

# Internal Core Imports
from src.core.constants import OrchestrationStatus

# Configure Logger for Dispatch Traceability
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
        self.token = os.getenv("GH_PAT")
        
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
        
        # --- LOGICAL WIRING ---
        # We ensure the payload includes the centralized IN_PROGRESS status.
        # This prevents the remote worker from having to "guess" the state.
        if "status" not in payload:
            payload["status"] = OrchestrationStatus.IN_PROGRESS.value

        data = {
            "event_type": "worker_trigger",
            "client_payload": payload
        }

        try:
            # Rule 4: Explicit or Error. 
            # We use direct key access to trigger a Hard-Halt if the payload is malformed.
            step_name = payload['step'] 
            logger.info(f"📡 Dispatching Signal: [{target_repo}] for Step [{step_name}]")
        except KeyError:
            logger.critical("Dispatch Payload missing 'step' key. Protocol Breach.")
            raise KeyError("❌ CRITICAL: Step ID missing from dispatch payload.")

        try:
            # Rule 5: Operational Hygiene - 15s timeout prevents hanging engine runners.
            response = requests.post(url, json=data, headers=self.headers, timeout=15)
            
            # GitHub API: 204 No Content indicates a successful dispatch request.
            if response.status_code == 204:
                logger.info(f"🚀 Signal Accepted: {target_repo} activation confirmed.")
                return True
            
            logger.error(f"❌ Handshake Refused: HTTP {response.status_code} - {response.text}")
            return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Connection Error during Dispatch to {target_repo}: {e}")
            return False