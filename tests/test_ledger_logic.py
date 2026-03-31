# tests/test_ledger_logic.py

from src.core.update_ledger import LedgerManager

def test_ledger_prepend_order(tmp_path):
    """Verifies that the ledger follows the 'Newest First' rule."""
    log_file = tmp_path / "performance_audit.md"
    ledger = LedgerManager(log_path=str(log_file))

    # Record two events
    ledger.record_event("FIRST", "This should be at the bottom")
    ledger.record_event("SECOND", "This should be at the top")

    with open(log_file, "r") as f:
        content = f.read()
        
    # Check that SECOND appears before FIRST
    assert content.find("SECOND") < content.find("FIRST")
    print("✅ Ledger Prepend Verified.")

def test_ledger_mapping_logic(tmp_path):
    """Verifies standardized dispatch logging format."""
    log_file = tmp_path / "performance_audit.md"
    ledger = LedgerManager(log_path=str(log_file))
    
    ledger.log_dispatch("p1", "m1", "solve", "org/repo")
    
    with open(log_file, "r") as f:
        content = f.read()
        
    assert "🚀 DISPATCH" in content
    assert "org/repo" in content
    print("✅ Dispatch Mapping Verified.")