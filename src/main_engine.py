# src/main_engine.py

import sys
import logging
from pathlib import Path
from src.core.bootloader import Bootloader
from src.api.github_trigger import Dispatcher
from src.core.update_ledger import LedgerManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

def run_engine():
    CONFIG_PATH = "config/active_disk.json"
    DATA_PATH = "data/testing-input-output/"
    ledger = LedgerManager()

    # 1. Boot & Auto-Wake
    try:
        state = Bootloader.mount(CONFIG_PATH, DATA_PATH)
        Bootloader.hydrate(state)
        ledger.record_event("📥 HYDRATION", "State successfully hydrated.")
    except Exception as e:
        logger.error(f"Boot Failure: {e}")
        sys.exit(1)

    # 2. Forensic Scan
    target_steps = state.forensic_artifact_scan()
    
    if not target_steps:
        logger.info("✅ MISSION COMPLETE: Pipeline Saturated. Entering Dormancy.")
        
        # Create the dormancy flag
        flag_path = Path("config/dormant.flag")
        flag_path.parent.mkdir(parents=True, exist_ok=True)
        with open(flag_path, "w") as f:
            f.write("STATE: SATURATED\nSTATUS: DORMANT")
            
        ledger.log_scan(state.project_id, "SATURATED_TERMINATED")
        return

    # 3. Dispatch
    logger.info(f"🔍 Gaps Detected: {len(target_steps)} tasks ready.")
    dispatcher = Dispatcher()
    
    for step in target_steps:
        payload = {
            "project_id": state.project_id,
            "manifest_id": state.manifest_data.get("manifest_id"),
            "step": step['name'],
            "requires": step['requires'],
            "produces": step['produces']
        }
        
        if dispatcher.trigger_worker(step['target_repo'], payload):
            ledger.log_dispatch(state.project_id, "N/A", step['name'], step['target_repo'])

if __name__ == "__main__":
    run_engine()