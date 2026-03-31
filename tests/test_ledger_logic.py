# tests/test_ledger_logic.py

import logging
from src.core.update_ledger import LedgerManager

# Standard logger setup for ledger logic
logger = logging.getLogger(__name__)

def test_ledger_prepend_order(tmp_path):
    """Verifies that the ledger follows the 'Newest First' rule."""
    logger.info("Running: test_ledger_prepend_order")
    
    log_file = tmp_path / "performance_audit.md"
    ledger = LedgerManager(log_path=str(log_file))

    # Record two events
    logger.debug("Recording FIRST event...")
    ledger.record_event("FIRST", "This should be at the bottom")
    
    logger.debug("Recording SECOND event...")
    ledger.record_event("SECOND", "This should be at the top")

    with open(log_file, "r") as f:
        content = f.read()
        
    # Check that SECOND appears before FIRST (Prepend logic)
    first_idx = content.find("FIRST")
    second_idx = content.find("SECOND")
    
    assert second_idx < first_idx
    logger.info(f"✅ Ledger Prepend Verified: SECOND (idx {second_idx}) is before FIRST (idx {first_idx}).")

def test_ledger_mapping_logic(tmp_path):
    """Verifies standardized dispatch logging format."""
    logger.info("Running: test_ledger_mapping_logic")
    
    log_file = tmp_path / "performance_audit.md"
    ledger = LedgerManager(log_path=str(log_file))
    
    logger.debug("Logging dispatch event for p1/m1...")
    ledger.log_dispatch("p1", "m1", "solve", "org/repo")
    
    with open(log_file, "r") as f:
        content = f.read()
        
    assert "🚀 DISPATCH" in content
    assert "org/repo" in content
    logger.info("✅ Dispatch Mapping Verified: Markdown string contains expected metadata.")