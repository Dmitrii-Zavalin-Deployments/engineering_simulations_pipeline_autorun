# src/main_engine.py

import sys
import requests
from core.state_engine import OrchestrationState
from api.github_trigger import Dispatcher

def run_engine():
    """
    The Main Entry Point.
    Phase C Compliance: Rule 3 - Orchestration Alignment.
    """
    CONFIG_PATH = "config/active_disk.json"
    DATA_PATH = "data/testing-input-output/"

    # 1. Initialize Ephemeral State (Phase C, Rule 0)
    state = OrchestrationState(CONFIG_PATH, DATA_PATH)
    print(f"🛰️ Engine Active: Project [{state.project_id}]")

    # 2. Remote Ingestion: Fetch the Manifest (Phase C, Rule 1)
    try:
        print(f"📥 Fetching Manifest: {state.manifest_url}")
        # Explicit timeout to prevent hung runners (Rule 5)
        response = requests.get(state.manifest_url, timeout=15)
        response.raise_for_status()
        state.hydrate_manifest(response.json())
    except Exception as e:
        print(f"❌ Critical: Manifest Ingestion Failed. {e}")
        sys.exit(1)

    # 3. Forensic Artifact Scan (Phase A Compliance)
    target_step = state.forensic_artifact_scan()

    # 4. Gate Evaluation (Phase C, Rule 3)
    if target_step:
        print(f"🚀 Logic Gate OPEN: Gap detected for {target_step['name']}")
        
        dispatcher = Dispatcher()
        
        # Rule 4: Access keys directly to ensure manifest integrity.
        # Payload carries the 'Artifact Signal' to the next worker.
        payload = {
            "project_id": state.project_id,
            "manifest_id": state.manifest_data["manifest_id"],
            "step": target_step['name']
        }
        
        success = dispatcher.trigger_worker(target_step['target_repo'], payload)
        
        if not success:
            print("❌ Critical: Worker dispatch failed.")
            sys.exit(1)
    else:
        print("✅ Logic Gate CLOSED: No execution required. Pipeline is saturated.")

if __name__ == "__main__":
    run_engine()