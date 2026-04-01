# src/main_engine.py

import sys
import logging
from src.core.bootloader import Bootloader
from src.api.github_trigger import Dispatcher
from src.core.update_ledger import LedgerManager

# Configure logging to ensure visibility during execution
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def run_engine():
    """
    Sovereign Lifecycle: The Periodic Pulse.
    Logic: Mount -> Hydrate -> Forensic Scan -> Dispatch -> Terminate.
    """
    CONFIG_PATH = "config/active_disk.json"
    DATA_PATH = "data/testing-input-output/"
    
    # Initialize Ledger (The Performance Audit Bridge)
    ledger = LedgerManager()

    # 1. Boot Sequence (Mounting & Hydration Gate)
    try:
        # Transforming URL into a living state object via Bootloader
        state = Bootloader.mount(CONFIG_PATH, DATA_PATH)
        Bootloader.hydrate(state)
        ledger.record_event("📥 HYDRATION", "Manifest successfully mounted from remote.")
    except Exception as e:
        error_msg = f"Boot/Hydration Failed: {str(e)}"
        ledger.record_event("❌ CRITICAL", error_msg)
        logger.error(error_msg)
        sys.exit(1)

    # 2. Forensic Discovery (The Gate Check)
    logger.debug("Starting forensic artifact scan...")
    target_step = state.forensic_artifact_scan()
    
    if target_step:
        ledger.log_scan(state.project_id, "GAP_DETECTED", gap=target_step['name'])
        logger.info(f"🔍 Gap Detected: target step '{target_step['name']}' requires execution.")
    else:
        ledger.log_scan(state.project_id, "SATURATED")
        logger.info("✅ State Saturated: No gaps found in artifacts. Mission complete.")
        return

    # 3. Dispatch (The Command Link)
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
            
    except Exception as e:
        ledger.record_event("❌ DISPATCH_ERROR", str(e))
        logger.error(f"Dispatch Runtime Error: {e}")
        sys.exit(1)

if __name__ == "__main__":  # pragma: no cover
    run_engine()