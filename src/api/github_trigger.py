# src/api/github_trigger.py

import os
import requests
from typing import Dict, Any

class Dispatcher:
    """
    The Command Link (Dispatch Protocol).
    Phase C Compliance: Rule 0 (__slots__) & Rule 3 (Remote Execution).
    """
    __slots__ = ['token', 'headers']

    def __init__(self):
        # Phase C: Rule 4 - Zero-Default Policy (Explicit or Error)
        # Standardized to GITHUB_TOKEN for nomadic environment compatibility
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError("❌ CRITICAL: GITHUB_TOKEN not found. Dispatch aborted.")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def trigger_worker(self, target_repo: str, payload: Dict[str, Any]) -> bool:
        """
        Sends a Repository Dispatch signal to the worker.
        Enforces the 'Periodic Pulse' by initiating and terminating.
        """
        url = f"https://api.github.com/repos/{target_repo}/dispatches"
        
        # Dispatch Protocol: Event type 'worker_trigger' is expected by worker repos
        data = {
            "event_type": "worker_trigger",
            "client_payload": payload
        }

        print(f"📡 Dispatching Signal: [{target_repo}] for Step [{payload.get('step')}]")

        try:
            # Phase C: Rule 1 - Resource Protection (Timeout enforced)
            response = requests.post(url, json=data, headers=self.headers, timeout=10)
            
            if response.status_code == 204:
                print(f"🚀 Signal Accepted: {target_repo} activation confirmed.")
                return True
            
            print(f"❌ Dispatch Failed [{response.status_code}]: {response.text}")
            return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection Error during Dispatch: {e}")
            return False