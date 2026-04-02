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
    - Rule 4: Zero-Default Policy (Hard-Halt on Failure)
    - Rule 5: Operational Hygiene (In-Flight Memory Management)
    """
    CONFIG_PATH = "config/active_disk.json"
    DATA_PATH = "data/testing-input-output/"
    FLAG_PATH = Path("config/dormant.flag")
    
    # Rule 0 & 4: Instantiate Ledger with zero-default path logic
    # LedgerManager now also handles the JSON Orchestration Memory
    ledger = LedgerManager(log_path="performance_audit.md")

    # 1. Boot & Auto-Wake
    try:
        state = Bootloader.mount(CONFIG_PATH, DATA_PATH)
        Bootloader.hydrate(state)
        ledger.record_event("📥 HYDRATION", "State successfully hydrated from Foundation.")
    except Exception as e:
        logger.critical(f"Boot Failure: {e}")
        sys.exit(1)

    # 2. Load In-Flight Memory
    orchestration_memory = ledger.load_orchestration_state()

    # 3. Forensic Scan (The IDENTIFY phase)
    # Pass the memory to the scan to filter out active workers
    target_steps = state.forensic_artifact_scan(orchestration_memory)
    
    # 4. Memory Cleanup (The HOUSEKEEPING phase)
    # If a job was in memory but forensic_artifact_scan didn't return it because 
    # its outputs are now present, we clear the lock.
    if orchestration_memory:
        for job_name in list(orchestration_memory.keys()):
            # Find the step definition in manifest
            step_def = next((s for s in state.manifest_data["pipeline_steps"] if s['name'] == job_name), None)
            if step_def:
                # Check if produced artifacts now exist
                outputs_exist = all((Path(DATA_PATH) / f).exists() for f in step_def['produces'])
                if outputs_exist:
                    ledger.clear_lock(job_name)
                    ledger.record_event("🔓 LOCK_RELEASE", f"Job {job_name} completed successfully. Lock cleared.")

    if not target_steps:
        logger.info("✅ MISSION COMPLETE: Pipeline Saturated or Workers In-Flight. Entering Dormancy.")
        
        # Only set DORMANT if there is absolutely no work and NO workers in flight
        active_memory = ledger.load_orchestration_state()
        if not active_memory:
            FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(FLAG_PATH, "w", encoding="utf-8") as f:
                f.write("STATUS: DORMANT")
            
        ledger.log_scan(
            state.project_id, 
            status="SATURATED_OR_WAITING", 
            gap="NONE"
        )
        return

    # 5. Active State Affirmation
    if FLAG_PATH.exists():
        FLAG_PATH.write_text("STATUS: ACTIVE", encoding="utf-8")

    # 6. Dispatch (The TRIGGER phase)
    logger.info(f"🔍 Gaps Detected: {len(target_steps)} tasks ready for pulse.")
    dispatcher = Dispatcher()
    all_dispatches_successful = True 
    
    for step in target_steps:
        try:
            manifest_id = state.manifest_data["manifest_id"]
            
            payload = {
                "project_id": state.project_id,
                "manifest_id": manifest_id,
                "step": step['name'],
                "requires": step['requires'],
                "produces": step['produces']
            }
            
            # Logic Gate: Signal the worker
            if dispatcher.trigger_worker(step['target_repo'], payload):
                # ledger.log_dispatch automatically updates the JSON memory to IN_PROGRESS
                ledger.log_dispatch(
                    project_id=state.project_id, 
                    manifest_id=manifest_id, 
                    step_name=step['name'], 
                    target_repo=step['target_repo'],
                    timeout_hours=step['timeout_hours']
                )
            else:
                logger.error(f"❌ DISPATCH FAILED: {step['target_repo']}")
                all_dispatches_successful = False

        except KeyError as e:
            logger.critical(f"Protocol Breach: Missing mandatory key {e}")
            raise KeyError(f"❌ CRITICAL: Data integrity failure. Missing {e}")

    # FINAL SAFETY CHECK
    if not all_dispatches_successful:
        logger.critical("🛑 ENGINE HALT: One or more dispatches failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_engine()