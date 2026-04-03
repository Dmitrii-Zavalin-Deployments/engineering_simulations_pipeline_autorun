# src/main_engine.py

import sys
import logging
from pathlib import Path

# Internal Core Imports
from src.core.constants import OrchestrationStatus, SystemPaths
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
    CONFIG_PATH = Path(SystemPaths.CONFIG_DIR) / SystemPaths.ACTIVE_DISK
    DATA_PATH = Path(SystemPaths.DATA_DIR)
    FLAG_PATH = Path(SystemPaths.CONFIG_DIR) / SystemPaths.DORMANT_FLAG
    
    # 1. Initialize Ledger Manager
    # Handles both Markdown Audit and JSON Orchestration Memory
    ledger = LedgerManager(log_path="performance_audit.md")

    # 2. Boot & Auto-Wake
    try:
        state = Bootloader.mount(str(CONFIG_PATH), str(DATA_PATH))
        Bootloader.hydrate(state)
        ledger.record_event("📥 HYDRATION", "State successfully hydrated from Foundation.")
    except Exception as e:
        logger.critical(f"Boot Failure: {e}")
        sys.exit(1)

    # 3. Load & Reconcile (The ROUND-AND-ROUND Phase)
    # We pull the current memory and let the state_engine heal it based on artifacts
    orchestration_data = ledger.load_orchestration_state()
    
    # Update the 'steps' portion of the ledger using our Transition Matrix
    updated_steps = state.reconcile_and_heal(orchestration_data.get("steps", {}))
    orchestration_data["steps"] = updated_steps
    
    # Save the 'Healed' state immediately
    # This ensures that even if dispatch fails, the ledger reflects the physical truth
    ledger.update_job_status("_ENGINE_PULSE_", "HEALED", {
        "project_id": state.project_id,
        "manifest_id": state.manifest_data["manifest_id"],
        "target": "INTERNAL",
        "timeout_hours": 0
    })
    ledger.log_scan(state.project_id, "Physical truth reconciled with ledger.")

    # 4. Identify Ready Tasks (The READY Phase)
    target_steps = state.get_ready_steps(updated_steps)

    if not target_steps:
        # Check if anything is still IN_PROGRESS (Workers in-flight)
        in_flight = any(s.get("status") == OrchestrationStatus.IN_PROGRESS.value 
                        for s in updated_steps.values())
        
        if not in_flight:
            logger.info("✅ MISSION COMPLETE: All tasks COMPLETED or WAITING. Setting DORMANT.")
            FLAG_PATH.write_text("STATUS: DORMANT", encoding="utf-8")
        else:
            logger.info("⏳ PULSE IDLE: Workers are currently in-flight. Staying ACTIVE.")
        return

    # 5. Active State Affirmation
    if FLAG_PATH.exists():
        FLAG_PATH.write_text("STATUS: ACTIVE", encoding="utf-8")

    # 6. Dispatch (The TRIGGER phase)
    logger.info(f"🚀 Pulse Detected: {len(target_steps)} tasks ready for activation.")
    dispatcher = Dispatcher()
    all_dispatches_successful = True 
    
    for step in target_steps:
        try:
            manifest_id = state.manifest_data["manifest_id"]
            
            payload = {
                "project_id": state.project_id,
                "manifest_id": manifest_id,
                "step": step['name'],
                "requires": step.get('requires', []),
                "produces": step.get('produces', [])
            }
            
            # Logic Gate: Trigger the GitHub Worker
            if dispatcher.trigger_worker(step['target_repo'], payload):
                # log_dispatch automatically updates the JSON memory to IN_PROGRESS
                ledger.log_dispatch(
                    project_id=state.project_id, 
                    manifest_id=manifest_id, 
                    step_name=step['name'], 
                    target_repo=step['target_repo'],
                    timeout_hours=step.get('timeout_hours', 6)
                )
            else:
                logger.error(f"❌ DISPATCH FAILED: {step['target_repo']}")
                all_dispatches_successful = False

        except KeyError as e:
            logger.critical(f"Protocol Breach: Missing mandatory key {e}")
            sys.exit(1)

    # FINAL SAFETY CHECK
    if not all_dispatches_successful:
        logger.critical("🛑 ENGINE HALT: One or more dispatches failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_engine()