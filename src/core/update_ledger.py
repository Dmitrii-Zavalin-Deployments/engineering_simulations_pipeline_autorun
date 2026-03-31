# src/core/update_ledger.py

import os
from datetime import datetime, timezone

class LedgerManager:
    """
    The Traceability Bridge (Performance Audit Ledger).
    Phase C Compliance: Rule 0 (__slots__) & Rule 5 (Performance Logging).
    """
    __slots__ = ['log_path']

    def __init__(self, log_path: str = "performance_audit.md"):
        self.log_path = log_path

    def record_event(self, category: str, message: str, metadata: dict = None):
        """
        Prepends a structured entry to the ledger.
        Format: [Timestamp UTC] [Category] Message | Metadata
        """
        # Using UTC for nomadic synchronization consistency
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        meta_str = f" | {metadata}" if metadata else ""
        
        header = "# 🛰️ Simulation Engine Performance Audit\n\n"
        new_entry = f"## [{timestamp}] {category}\n- **Message:** {message}{meta_str}\n\n---\n\n"

        # Read existing content to prepend
        existing_content = ""
        if os.path.exists(self.log_path):
            try:
                current_text = open(self.log_path, "r", encoding="utf-8").read()
                # Remove header from old content to avoid duplication during prepend
                existing_content = current_text.replace(header, "")
            except Exception:
                existing_content = ""

        # Phase C: Rule 1 - Resource Protection (Atomic Write with Explicit Encoding)
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(header + new_entry + existing_content)

    def log_dispatch(self, project_id: str, manifest_id: str, step_name: str, target_repo: str):
        """Standardized mapping for Dispatch events."""
        self.record_event(
            category="🚀 DISPATCH",
            message=f"Worker activated for step: {step_name}",
            metadata={
                "project_id": project_id,
                "manifest_id": manifest_id,
                "target": target_repo
            }
        )

    def log_scan(self, project_id: str, status: str, gap: str = None):
        """Standardized mapping for Forensic Scan results."""
        msg = f"Scan Result: {status}"
        if gap:
            msg += f" | Gap detected at: {gap}"
            
        self.record_event(
            category="🔍 FORENSIC_SCAN",
            message=msg,
            metadata={"project_id": project_id}
        )