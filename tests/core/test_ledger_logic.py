# tests/core/test_ledger_logic.py

import logging
from src.core.update_ledger import LedgerManager

logger = logging.getLogger(__name__)

def test_ledger_prepend_order(tmp_path):
    """Verifies that the ledger follows the 'Newest First' rule for nomadic monitoring."""
    log_file = tmp_path / "performance_audit.md"
    ledger = LedgerManager(log_path=str(log_file))

    # Record sequence
    ledger.record_event("FIRST", "Bottom entry")
    ledger.record_event("SECOND", "Top entry")

    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert content.find("SECOND") < content.find("FIRST")
    logger.info("✅ Prepend Order Verified: Newest pulses are at the top.")

def test_audit_consistency_sequence(tmp_path):
    """VERIFICATION: A run must reflect the full SCAN -> DISPATCH sequence."""
    log_file = tmp_path / "performance_audit.md"
    ledger = LedgerManager(log_path=str(log_file))
    
    project = "navier_stokes_alpha_01"
    
    # 1. SCAN phase
    ledger.log_scan(project, "GAP_DETECTED", gap="navier_stokes_solver")
    
    # 2. DISPATCH phase

    ledger.log_dispatch(project, "m1_stable", "navier_stokes_solver", "org/repo", 6)
    
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "🔍 FORENSIC_SCAN" in content
    assert "🚀 DISPATCH" in content
    assert "navier_stokes_solver" in content
    logger.info("✅ Audit Traceability Verified: Full sequence is intact.")