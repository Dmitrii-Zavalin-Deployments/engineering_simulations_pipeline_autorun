# src/main_engine.py

import sys
import requests
from src.core.state_engine import OrchestrationState
from src.api.github_trigger import Dispatcher

def run_engine():
    """
    Sovereign Lifecycle: The Periodic Pulse.
    Logic: Mount -> Forensic Scan -> Dispatch -> Terminate.
    Phase C, Section 2: The Isolation Mandate.
    """
    # Pathing aligned with nomadic local structure
    CONFIG_PATH = "config/active_disk.json"
    DATA_PATH = "data/testing-input-output/"

    # 1. Ephemeral Initialization (Foundation Mounting)
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
    # The 'Gate' only opens if Inputs exist AND Outputs are missing.
    target_step = state.forensic_artifact_scan()

    # 4. Dispatch (The Command Link)
    if target_step:
        try:
            dispatcher = Dispatcher()
            
            # Construct JSON Payload for the nomadic worker
            payload = {
                "project_id": state.project_id,
                "manifest_id": state.manifest_data["manifest_id"],
                "step": target_step['name'],
                "requires": target_step['requires'],
                "produces": target_step['produces']
            }
            
            # Trigger worker and terminate (Non-blocking pulse)
            success = dispatcher.trigger_worker(target_step['target_repo'], payload)
            if not success:
                sys.exit(1)
                
            print(f"🚀 Dispatch Successful: Worker [{target_step['target_repo']}] activated.")
            
        except RuntimeError as e:
            print(e)
            sys.exit(1)
    else:
        # Saturated state prevents "Double-Spend" of compute resources.
        print("🏁 Mission Saturated: Logic Gates are all closed. Standing down.")

if __name__ == "__main__":
    run_engine()