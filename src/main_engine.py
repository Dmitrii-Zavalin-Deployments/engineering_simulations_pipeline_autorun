# src/main_engine.py

"""
Archivist I/O: Main Execution Engine.

Compliance:
- Rule 5 (Deterministic Init): Configuration paths are explicitly defined.
- Rule 8 (API Minimalism): Single entry point via run_engine().
"""

import sys
import logging
import requests
from src.core.state_engine import OrchestrationState
from src.api.github_trigger import Dispatcher
from src.core.update_ledger import LedgerManager

# Standard logger setup for the engine
logger = logging.getLogger(__name__)

def run_engine():
    """
    Sovereign Lifecycle: The Periodic Pulse.
    Logic: Mount -> Forensic Scan -> Dispatch -> Terminate.
    Phase C, Section 2: The Isolation Mandate.
    """
    # Pathing aligned with nomadic local structure
    CONFIG_PATH = "config/active_disk.json"
    DATA_PATH = "data/testing-input-output/"
    
    # Initialize Ledger (The Performance Audit Bridge)
    ledger = LedgerManager()

    # 1. Ephemeral Initialization (Foundation Mounting)
    try:
        state = OrchestrationState(CONFIG_PATH, DATA_PATH)
        logger.info(f"🛰️ Engine Active: [{state.project_id}]")
    except Exception as e:
        logger.critical(f"Failed to initialize OrchestrationState: {e}")
        sys.exit(1)

    # 2. Remote Manifest Acquisition (External Authority)
    try:
        logger.info(f"📥 Fetching Manifest: {state.manifest_url}")
        response = requests.get(state.manifest_url, timeout=15)
        response.raise_for_status()
        
        state.hydrate_manifest(response.json())
        ledger.record_event("📥 HYDRATION", "Manifest successfully mounted from remote.")
        logger.debug("Manifest hydration complete.")
        
    except Exception as e:
        error_msg = f"Manifest Acquisition Failed: {str(e)}"
        ledger.record_event("❌ CRITICAL", error_msg)
        logger.error(error_msg)
        sys.exit(1)

    # 3. Forensic Discovery (Idempotency Contract)
    # The 'Gate' only opens if Inputs exist AND Outputs are missing.
    logger.debug("Starting forensic artifact scan...")
    target_step = state.forensic_artifact_scan()
    
    if target_step:
        ledger.log_scan(state.project_id, "GAP_DETECTED", gap=target_step['name'])
        logger.info(f"🔍 Gap Detected: target step '{target_step['name']}' requires execution.")
    else:
        ledger.log_scan(state.project_id, "SATURATED")
        logger.info("✅ State Saturated: No gaps found in artifacts.")

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
            
            logger.info(f"🚀 Dispatching payload to {target_step['target_repo']}...")
            
            # Trigger worker and terminate (Non-blocking pulse)
            success = dispatcher.trigger_worker(target_step['target_repo'], payload)
            
            if success:
                ledger.log_dispatch(
                    state.project_id, 
                    state.manifest_data["manifest_id"], 
                    target_step['name'], 
                    target_step['target_repo']
                )
                logger.info(f"✅ Dispatch Successful: {target_step['name']}")
            else:
                logger.error(f"❌ Dispatch failed for step: {target_step['name']}")
                sys.exit(1)
                
        except RuntimeError as e:
            ledger.record_event("❌ DISPATCH_ERROR", str(e))
            logger.error(f"Dispatch Runtime Error: {e}")
            sys.exit(1)
    else:
        # Saturated state prevents "Double-Spend" of compute resources.
        logger.info("🏁 Mission Saturated: Logic Gates are all closed. Standing down.")

if __name__ == "__main__":  # pragma: no cover
    # Note: Ensure basicConfig is set at the entry point of your app to see these logs
    run_engine()