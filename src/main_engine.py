# src/main_engine.py

import sys
import os
import requests
from core.state_engine import OrchestrationState

def main():
    # Paths governed by the 'Single-Slot' Rule
    CONFIG = "config/active_disk.json"
    DATA_ROOT = "data/testing-input-output/"

    print("--- 🛰️ Artifact-Driven Engine: Booting ---")
    
    # 1. Mount Disk & Initialize Ephemeral State
    try:
        state = OrchestrationState(CONFIG, DATA_ROOT)
        print(f"✅ Disk Mounted: Project [{state.project_id}]")
    except Exception as e:
        print(f"❌ Critical Failure: Could not mount disk. {e}")
        sys.exit(1)

    # 2. Manifest Ingestion (Simplified for initial version)
    # In full implementation, this fetches from state.manifest_url
    # For now, we define a local mock to verify the Logic Gate
    mock_manifest = {
        "pipeline_steps": [
            {
                "name": "navier_stokes_solver",
                "target_repo": "navier-stokes-solver",
                "requires": ["geometry.msh"],
                "produces": ["results.zip"]
            }
        ]
    }
    state.hydrate_manifest(mock_manifest)

    # 3. Forensic Artifact Scan
    target_step = state.forensic_artifact_scan()

    # 4. Gate Evaluation & Dispatch
    if target_step:
        print(f"🚀 Logic Gate OPEN: Dispatching to {target_step['target_repo']}")
        # Dispatch logic to follow in src/api/github_trigger.py
    else:
        print("💤 Logic Gate CLOSED: No execution required.")

if __name__ == "__main__":
    main()