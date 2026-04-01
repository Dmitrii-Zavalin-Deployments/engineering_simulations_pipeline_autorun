# src/core/update_ledger.py

import os
import logging
from datetime import datetime, timezone

# Configure Logger for Engine Traceability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("Engine.Ledger")

class LedgerManager:
    """
    The Traceability Bridge (Performance Audit Ledger).
    Phase C Compliance: Rule 0 (__slots__) & Rule 5 (Performance Logging).
    Optimization: Platinum-grade deterministic error handling & Atomic Prepending.
    """
    __slots__ = ['log_path']

    def __init__(self, log_path: str = "performance_audit.md"):
        self.log_path = log_path

    def record_event(self, category: str, message: str, metadata: dict = None):
        """
        Prepends a structured entry to the ledger.
        Ensures the 'Pulse' history remains chronological (Newest First).
        """
        # Using UTC for nomadic synchronization consistency
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        meta_str = f" | {metadata}" if metadata else ""
        
        header = "# 🛰️ Simulation Engine Performance Audit\n\n"
        new_entry = f"## [{timestamp}] {category}\n- **Message:** {message}{meta_str}\n\n---\n\n"

        existing_content = ""
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    current_text = f.read()
                    # Remove header from old content to avoid duplication during prepend
                    existing_content = current_text.replace(header, "")
            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Ledger Read Warning: {e}. Starting fresh buffer.")
                existing_content = ""

        # Phase C: Rule 1 - Resource Protection (Atomic Write with Explicit Encoding)
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write(header + new_entry + existing_content)
        except IOError as e:
            logger.error(f"Critical Ledger Write Failure: {e}")

    def log_scan(self, project_id: str, status: str, gap: str = "NONE"):
        """Standardized mapping for Forensic Scan results (The IDENTIFY phase)."""
        msg = f"Forensic Scan Result: {status}"
        if gap != "NONE":
            msg += f" | Target Step Found: {gap}"
        
        logger.info(f"🔍 Forensic Scan [{project_id}]: {status}")
        self.record_event(
            category="🔍 FORENSIC_SCAN",
            message=msg,
            metadata={"project_id": project_id, "gap_identified": gap}
        )

    def log_dispatch(self, project_id: str, manifest_id: str, step_name: str, target_repo: str):
        """Standardized mapping for Dispatch events (The DISPATCH phase)."""
        logger.info(f"🚀 Dispatching Worker: {step_name} -> {target_repo}")
        self.record_event(
            category="🚀 DISPATCH",
            message=f"Command Link Handshake Confirmed for step: {step_name}",
            metadata={
                "project_id": project_id,
                "manifest_id": manifest_id,
                "target": target_repo
            }
        )