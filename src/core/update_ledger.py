# src/core/update_ledger.py

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict

# Configure Logger for Engine Traceability
logger = logging.getLogger("Engine.Ledger")

class LedgerManager:
    """
    The Traceability Bridge (Performance Audit Ledger).
    Phase C Compliance: 
    - Rule 0: __slots__ Mandatory Architecture
    - Rule 4: Zero-Default Policy (Explicit or Error)
    - Rule 5: Operational Hygiene (Audit Trail)
    """
    
    # Rule 0: Eliminate dict overhead for nomadic scalability
    __slots__ = ['log_path', 'header']

    def __init__(self, log_path: str = "performance_audit.md"):
        self.log_path = log_path
        self.header = "# 🛰️ Simulation Engine Performance Audit\n\n"

    def record_event(self, category: str, message: str, metadata: Optional[Dict] = None):
        """
        Prepends a structured entry to the ledger using Atomic Prepending.
        Ensures the 'Pulse' history remains chronological (Newest First).
        """
        # Rule 5: Using UTC for nomadic synchronization consistency
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        meta_str = f" | {metadata}" if metadata else ""
        
        new_entry = f"## [{timestamp}] {category}\n- **Message:** {message}{meta_str}\n\n---\n\n"

        existing_content = ""
        if os.path.exists(self.log_path):
            try:
                # Rule 1: Explicit Encoding Mandate
                with open(self.log_path, "r", encoding="utf-8") as f:
                    current_text = f.read()
                    # Strip existing header to avoid duplication during the prepend cycle
                    existing_content = current_text.replace(self.header, "")
            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Ledger Read Warning: {e}. Re-initializing buffer.")
                existing_content = ""

        # Phase C: Rule 1 & 5 - Resource Protection (Atomic Write)
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write(self.header + new_entry + existing_content)
        except IOError as e:
            # Rule 4: Hard-Halt on critical I/O failure
            logger.critical(f"Critical Ledger Write Failure: {e}")
            raise RuntimeError(f"❌ CRITICAL: Could not update audit ledger. {e}")

    def log_scan(self, project_id: str, status: str, gap: str):
        """
        Standardized mapping for Forensic Scan results (The IDENTIFY phase).
        Rule 4 Correction: 'gap' is now required to prevent silent default logic.
        """
        msg = f"Forensic Scan Result: {status} | Target: {gap}"
        
        logger.info(f"🔍 Forensic Scan [{project_id}]: {status}")
        self.record_event(
            category="🔍 FORENSIC_SCAN",
            message=msg,
            metadata={"project_id": project_id, "gap_identified": gap}
        )

    def log_dispatch(self, project_id: str, manifest_id: str, step_name: str, target_repo: str):
        """
        Standardized mapping for Dispatch events (The DISPATCH phase).
        Rule 4: Explicit key passing for manifest_id and project_id.
        """
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