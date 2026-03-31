# src/main_engine.py

import sys
import requests
from src.core.state_engine import OrchestrationState
from src.api.github_trigger import Dispatcher

def run_engine():
    """
    The Sovereign Orchestrator Execution Cycle.
    """
    CONFIG_PATH = "config/active_disk.json"
    DATA_PATH = "data/testing-input-output/"

    # 1. Initialize Console (Zero-Knowledge)
    state = OrchestrationState(CONFIG_PATH, DATA_PATH)
    print(f"🛰️ Engine Active: Project [{state.project_id}]")

    # 2. Disc Ingestion (External Authority)
    try:
        print(f"📥 Mounting Remote Disc: {state.manifest_url}")
        response = requests.get(state.manifest_url, timeout=15)
        response.raise_for_status()
        
        # Hydration: Turning JSON into Living Logic
        state.hydrate_manifest(response.json())
    except Exception as e:
        print(f"❌ Critical: Mounting Failed. {e}")
        sys.exit(1)

    # 3. Forensic Scan & Dispatch
    target_step = state.forensic_artifact_scan()

    if target_step:
        dispatcher = Dispatcher()
        payload = {
            "project_id": state.project_id,
            "manifest_id": state.manifest_data["manifest_id"],
            "step": target_step['name']
        }
        
        if dispatcher.trigger_worker(target_step['target_repo'], payload):
            print(f"🚀 Signal Sent to Worker: {target_step['target_repo']}")
        else:
            sys.exit(1)
    else:
        print("✅ Pipeline Saturated. No action required.")

if __name__ == "__main__":
    run_engine()