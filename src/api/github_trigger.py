# src/api/github_trigger.py

import os
import requests

class Dispatcher:
    """
    Sends the repository_dispatch signal to worker repositories.
    Phase C: Rule 0 Compliance (Memory Efficiency via __slots__).
    """
    __slots__ = ['headers']

    def __init__(self):
        # Phase C: Rule 4 - Zero-Default Policy (Explicit or Error)
        token = os.getenv("GH_PAT")
        if not token:
            raise EnvironmentError("CRITICAL: GH_PAT secret is missing. Orchestration aborted.")
        
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def trigger_worker(self, full_repo_path: str, payload: dict) -> bool:
        """
        Triggers the 'orchestrator_trigger' event in the target repo.
        Follows the Sovereign Lifecycle for worker activation.
        """
        url = f"https://api.github.com/repos/{full_repo_path}/dispatches"
        data = {
            "event_type": "orchestrator_trigger",
            "client_payload": payload
        }
        
        # Phase C: Rule 1 - Resource Protection
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            
            if response.status_code == 204:
                print(f"✅ Dispatch Successful: {full_repo_path} activated.")
                return True
            
            print(f"❌ Dispatch Failed [{response.status_code}]: {response.text}")
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error during Dispatch: {e}")
            return False