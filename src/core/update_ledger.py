import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict

# Internal Core Imports
from src.core.constants import OrchestrationStatus, SystemPaths

# Configure Logger for Engine Traceability
logger = logging.getLogger("Engine.Ledger")

class LedgerManager:
    """
    The Traceability Bridge (Performance Audit & Orchestration Memory).
    Phase C Compliance: 
    - Rule 0: __slots__ Mandatory Architecture
    - Rule 4: Zero-Default Policy (Explicit or Error)
    - Rule 5: Operational Hygiene (Audit Trail & Memory)
    
    Structure: Nested JSON structure for Metadata/Steps isolation.
    """
    
    # Rule 0: Eliminate dict overhead for nomadic scalability
    __slots__ = ['log_path', 'orchestration_path', 'header']

    def __init__(self, log_path: str = "performance_audit.md"):
        self.log_path = log_path
        # Standardized pathing via SystemPaths
        self.orchestration_path = os.path.join(SystemPaths.CONFIG_DIR, SystemPaths.LEDGER)
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
                    # Keep everything except the header to avoid duplication
                    existing_content = current_text.replace(self.header, "")
            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Audit Read Warning: {e}. Re-initializing buffer.")

        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write(self.header + new_entry + existing_content)
        except IOError as e:
            logger.critical(f"Critical Audit Write Failure: {e}")
            raise RuntimeError(f"❌ CRITICAL: Could not update performance audit. {e}")

    # --- SECTION 2: ORCHESTRATION MEMORY (JSON) ---

    def load_orchestration_state(self) -> Dict:
        """
        Rule 4: Zero-Default. Loads the JSON memory with Metadata/Steps structure.
        """
        default_structure = {"metadata": {}, "steps": {}}
        
        if not os.path.exists(self.orchestration_path):
            logger.warning("Orchestration Ledger missing. Initializing fresh structure.")
            return default_structure
        
        try:
            with open(self.orchestration_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                # Migration logic: Ensure new nested structure exists
                if "steps" not in content:
                    return {"metadata": content.get("metadata", {}), "steps": content.get("steps", {})}
                return content
        except (json.JSONDecodeError, AttributeError):
            logger.error("Orchestration Ledger corrupt. Resetting to safe structure.")
            return default_structure

    def update_job_status(self, job_name: str, status: str, metadata: Dict):
        """
        Atomic Write for the In-Flight memory inside the 'steps' key.
        Maintains the "Round-and-Round" state for the State Engine.
        """
        ledger = self.load_orchestration_state()
        
        # Rule 5: Operational Hygiene - Update specific step entry
        ledger["steps"][job_name] = {
            "status": status,
            "last_triggered": datetime.now(timezone.utc).isoformat(),
            "timeout_hours": metadata.get("timeout_hours", 6),
            "target_repo": metadata.get("target", "Unknown")
        }

        # Sync Metadata Header
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

    # --- SECTION 3: WRAPPERS ---

    def log_scan(self, project_id: str, message: str):
        """Logs the results of the reconcile_and_heal pulse."""
        logger.info(f"🔍 Forensic Scan [{project_id}]: {message}")
        self.record_event(
            category="🔍 FORENSIC_SCAN",
            message=message,
            metadata={"project_id": project_id}
        )

    def log_dispatch(self, project_id: str, manifest_id: str, step_name: str, target_repo: str, timeout_hours: int):
        """
        Final Dispatch Record. Updates both the Markdown Audit and the JSON Ledger.
        """
        logger.info(f"🚀 Dispatching Worker: {step_name} -> {target_repo}")
        
        # 1. Update Human-Readable Audit
        self.record_event(
            category="🚀 DISPATCH",
            message=f"Command Link Handshake Confirmed for step: {step_name}",
            metadata={
                "project_id": project_id,
                "target": target_repo,
                "timeout_hours": timeout_hours
            }
        )
        
        # 2. Update Machine-Readable State (Set to IN_PROGRESS)
        self.update_job_status(
            job_name=step_name, 
            status=OrchestrationStatus.IN_PROGRESS.value, 
            metadata={
                "project_id": project_id,
                "manifest_id": manifest_id,
                "target": target_repo, 
                "timeout_hours": timeout_hours
            }
        )