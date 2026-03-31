# src/core/update_ledger.py

import sys
import datetime
from pathlib import Path

def update_ledger(status: str):
    """
    The Archivist: Records every orchestration cycle.
    Phase C Compliance: Rule 5 - Performance Logging.
    """
    ledger = Path("performance_audit.md")
    # Using UTC for nomadic synchronization
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    header = "# 🛰️ Simulation Engine Performance Audit\n\n"
    entry = (
        f"### Audit: {now}\n"
        f"- **Cycle Status:** {status}\n"
        f"- **Scope:** Forensic Logic Evaluation\n"
        f"---\n\n"
    )

    # Phase C: Rule 1 - Resource Protection (Explicit encoding)
    if ledger.exists():
        current_text = ledger.read_text(encoding="utf-8")
        # Ensure we don't duplicate the header while prepending
        content = current_text.replace(header, "")
        ledger.write_text(header + entry + content, encoding="utf-8")
    else:
        ledger.write_text(header + entry, encoding="utf-8")

if __name__ == "__main__":
    # Phase C: Rule 4 - Explicit or Error. 
    # The status must be passed by the GitHub Action runner.
    try:
        job_status = sys.argv[1]
    except IndexError:
        print("❌ Critical: Ledger update failed. No status provided.")
        sys.exit(1)
        
    update_ledger(job_status)