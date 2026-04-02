# src/core/update_ledger.py

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict

# Configure Logger for Engine Traceability
logger = logging.getLogger("Engine.Ledger")

class LedgerManager:
    """
    The Traceability Bridge (Performance Audit & Orchestration Memory).
    Phase C Compliance: 
    - Rule 0: __slots__ Mandatory Architecture
    - Rule 4: Zero-Default Policy (Explicit or Error)
    - Rule 5: Operational Hygiene (Audit Trail & Memory)
    
    Updated: Nested JSON structure support for Metadata/Steps isolation.
    """
    
    # Rule 0: Eliminate dict overhead for nomadic scalability
    __slots__ = ['log_path', 'orchestration_path', 'header']

    def __init__(self, log_path: str = "performance_audit.md", orchestration_path: str = "config/orchestration_ledger.json"):
        self.log_path = log_path
        self.orchestration_path = orchestration_path
        self.header = "# 🛰️ Simulation Engine Performance Audit\n\n"

    # --- SECTION 1: PERFORMANCE AUDIT (MARKDOWN) ---

    def record_event(self, category: str, message: str, metadata: Optional[Dict] = None):
        """
        Prepends a structured entry to the ledger using Atomic Prepending.
        Ensures the 'Pulse' history remains chronological (Newest First).
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        meta_str = f" | {metadata}" if metadata else ""
        
        new_entry = f"## [{timestamp}] {category}\n- **Message:** {message}{meta_str}\n\n---\n\n"

        existing_content = ""
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    current_text = f.read()
                    existing_content = current_text.replace(self.header, "")
            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Ledger Read Warning: {e}. Re-initializing buffer.")
                existing_content = ""

        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write(self.header + new_entry + existing_content)
        except IOError as e:
            logger.critical(f"Critical Ledger Write Failure: {e}")
            raise RuntimeError(f"❌ CRITICAL: Could not update audit ledger. {e}")

    # --- SECTION 2: ORCHESTRATION MEMORY (JSON) ---

    def load_orchestration_state(self) -> Dict:
        """
        Rule 4: Zero-Default. Loads the JSON memory with Metadata/Steps structure.
        """
        if not os.path.exists(self.orchestration_path):
            logger.warning("Orchestration Ledger missing. Initializing empty structure.")
            return {"metadata": {}, "steps": {}}
        
        try:
            with open(self.orchestration_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                # Ensure the new structure exists even if reading an old-style file
                if "steps" not in content:
                    return {"metadata": content.get("metadata", {}), "steps": {}}
                return content
        except json.JSONDecodeError:
            logger.error("Orchestration Ledger corrupt. Resetting to safe structure.")
            return {"metadata": {}, "steps": {}}

    def update_job_status(self, job_name: str, status: str, metadata: Dict):
        """
        Atomic Write for the In-Flight memory inside the 'steps' key.
        Preserves existing metadata while updating the job lock.
        """
        ledger = self.load_orchestration_state()
        
        # Rule 5: Operational Hygiene - Update specific step entry
        ledger["steps"][job_name] = {
            "status": status,
            "last_triggered": datetime.now(timezone.utc).isoformat(),
            "timeout_hours": metadata["timeout_hours"],
            "target_repo": metadata["target"]
        }

        # If project/manifest info is provided in metadata, ensure it's in the header
        if "project_id" in metadata:
            ledger["metadata"]["project_id"] = metadata["project_id"]
        if "manifest_id" in metadata:
            ledger["metadata"]["manifest_id"] = metadata["manifest_id"]

        try:
            os.makedirs(os.path.dirname(self.orchestration_path), exist_ok=True)
            with open(self.orchestration_path, "w", encoding="utf-8") as f:
                json.dump(ledger, f, indent=2)
        except IOError as e:
            logger.critical(f"Failed to write to Orchestration Ledger: {e}")

    def clear_lock(self, job_name: str):
        """
        Removes a job from the 'steps' memory once artifacts are detected.
        """
        ledger = self.load_orchestration_state()
        if job_name in ledger["steps"]:
            logger.info(f"🔓 Releasing In-Flight Lock: {job_name}")
            del ledger["steps"][job_name]
            try:
                with open(self.orchestration_path, "w", encoding="utf-8") as f:
                    json.dump(ledger, f, indent=2)
            except IOError as e:
                logger.error(f"Failed to clear lock in JSON memory: {e}")

    # --- SECTION 3: WRAPPERS ---

    def log_scan(self, project_id: str, status: str, gap: str):
        msg = f"Forensic Scan Result: {status} | Target: {gap}"
        logger.info(f"🔍 Forensic Scan [{project_id}]: {status}")
        self.record_event(
            category="🔍 FORENSIC_SCAN",
            message=msg,
            metadata={"project_id": project_id, "gap_identified": gap}
        )

    def log_dispatch(self, project_id: str, manifest_id: str, step_name: str, target_repo: str, timeout_hours: int):
        """
        Phase C Fix: Updated to pass project/manifest IDs to the ledger update.
        """
        logger.info(f"🚀 Dispatching Worker: {step_name} -> {target_repo}")
        self.record_event(
            category="🚀 DISPATCH",
            message=f"Command Link Handshake Confirmed for step: {step_name}",
            metadata={
                "project_id": project_id,
                "manifest_id": manifest_id,
                "target": target_repo,
                "timeout_hours": timeout_hours
            }
        )
        
        # Rule 5: Automatically update the In-Flight JSON memory on dispatch
        self.update_job_status(
            job_name=step_name, 
            status="IN_PROGRESS", 
            metadata={
                "project_id": project_id,
                "manifest_id": manifest_id,
                "target": target_repo, 
                "timeout_hours": timeout_hours
            }
        )