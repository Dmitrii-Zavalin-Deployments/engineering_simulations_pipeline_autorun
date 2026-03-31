# src/main_engine.py

import sys
import requests
from src.core.state_engine import OrchestrationState
from src.api.github_trigger import Dispatcher

def run_engine():
    """
    Sovereign Lifecycle: Download -> Evaluate -> Dispatch.
    Phase C, Section 2: The Isolation Mandate.
    """
    # Paths aligned with dmitrii@computer directory structure
    CONFIG_PATH = "config/active_disk.json"
    DATA_PATH = "data/testing-input-output/"

    # 1. Ephemeral Initialization
    state = OrchestrationState(CONFIG_PATH, DATA_PATH)
    print(f"🛰️ Engine Active: [{state.project_id}]")

    # 2. Remote Manifest Acquisition (External Authority)
    try:
        print(f"📥 Fetching Manifest: {state.manifest_url}")
        response = requests.get(state.manifest_url, timeout=15)
        response.raise_for_status()
        state.hydrate_manifest(response.json())
    except Exception as e:
        print(f"❌ Critical: Manifest Acquisition Failed: {e}")
        sys.exit(1)

    # 3. Forensic Discovery (Idempotency Contract)
    target_step = state.forensic_artifact_scan()

    # 4. Logic Gate & Dispatch
    if target_step:
        dispatcher = Dispatcher()
        payload = {
            "project_id": state.project_id,
            "manifest_id": state.manifest_data["manifest_id"],
            "step": target_step['name']
        }
        
        # Trigger the remote worker (Nomadic Execution)
        success = dispatcher.trigger_worker(target_step['target_repo'], payload)
        if not success:
            print(f"❌ Dispatch Failed for step: {target_step['name']}")
            sys.exit(1)
        print(f"🚀 Dispatch Successful: {target_step['name']}")
    else:
        # Saturated state: All artifacts found.
        print("🏁 Mission Complete: Logic Gates are all closed.")

if __name__ == "__main__":
    run_engine()