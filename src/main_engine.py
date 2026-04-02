# src/main_engine.py

import sys
import logging
from pathlib import Path
from src.core.bootloader import Bootloader
from src.api.github_trigger import Dispatcher
from src.core.update_ledger import LedgerManager

# Rule 5: Standardized Logging Format for Audit Trail
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("Engine.Main")

def run_engine():
    """
    The Sovereign Logic Gate.
    Phase C Compliance:
    - Rule 1: Isolation Mandate (Defined Paths)
    - Rule 4: Zero-Default Policy (Hard-Halt on Missing Data)
    - Rule 5: Operational Hygiene (Dormancy Lifecycle)
    """
    CONFIG_PATH = "config/active_disk.json"
    DATA_PATH = "data/testing-input-output/"
    FLAG_PATH = Path("config/dormant.flag")
    
    # Rule 0 & 4: Instantiate Ledger with zero-default path logic
    ledger = LedgerManager(log_path="performance_audit.md")

    # 1. Boot & Auto-Wake
    try:
        # Rule 1: Environmental hydration from the 'Foundation' (Disk)
        # Bootloader.mount now handles time-based auto-wake via active_disk.json
        state = Bootloader.mount(CONFIG_PATH, DATA_PATH)
        Bootloader.hydrate(state)
        ledger.record_event("📥 HYDRATION", "State successfully hydrated from Foundation.")
    except Exception as e:
        logger.critical(f"Boot Failure: {e}")
        # Rule 4: Hard-Halt on boot failure
        sys.exit(1)

    # 2. Forensic Scan (The IDENTIFY phase)
    # Rule 5: Scans local artifacts to determine the 'Gap'
    target_steps = state.forensic_artifact_scan()
    
    if not target_steps:
        logger.info("✅ MISSION COMPLETE: Pipeline Saturated. Entering Dormancy.")
        
        # Rule 5: Generate Dormancy Flag for the Gatekeeper (Simplified STATUS)
        FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(FLAG_PATH, "w", encoding="utf-8") as f:
            f.write("STATUS: DORMANT")
            
        ledger.log_scan(
            project_id=state.project_id, 
            status="SATURATED_TERMINATED", 
            gap="NONE"
        )
        return

    # 3. Active State Affirmation
    # If we have work to do, ensure the flag reflects ACTIVE status
    if FLAG_PATH.exists():
        FLAG_PATH.write_text("STATUS: ACTIVE", encoding="utf-8")

    # 4. Dispatch (The TRIGGER phase)
    logger.info(f"🔍 Gaps Detected: {len(target_steps)} tasks ready.")
    dispatcher = Dispatcher()
    
    for step in target_steps:
        # Rule 4 Violation Correction: Direct key access ensures crash on data integrity failure.
        try:
            manifest_id = state.manifest_data["manifest_id"]
            
            payload = {
                "project_id": state.project_id,
                "manifest_id": manifest_id,
                "step": step['name'],
                "requires": step['requires'],
                "produces": step['produces']
            }
            
            if dispatcher.trigger_worker(step['target_repo'], payload):
                ledger.log_dispatch(
                    project_id=state.project_id, 
                    manifest_id=manifest_id, 
                    step_name=step['name'], 
                    target_repo=step['target_repo']
                )
        except KeyError as e:
            # Rule 4: Zero-Default means we do NOT proceed with a fallback ID
            logger.critical(f"Protocol Breach: Missing mandatory key {e}")
            raise KeyError(f"❌ CRITICAL: Data integrity failure in Manifest. Missing {e}")

if __name__ == "__main__":
    run_engine()