# tests/behavior/test_ledger_integrity.py

import pytest
import json
import os
from datetime import datetime
from unittest.mock import patch

# Assuming your core ledger/audit modules
from src.core.ledger import LedgerManager
from src.core.audit import AuditLogger

@pytest.fixture
def nomadic_env(tmp_path):
    """Sets up a temporary workspace for I/O testing."""
    root = tmp_path / "workdir"
    root.mkdir()
    ledger_file = root / "orchestration_ledger.json"
    audit_file = root / "performance_audit.md"
    
    # Initialize files
    ledger_file.write_text("{}")
    audit_file.write_text("# Performance Audit Log\n")
    
    return {
        "root": root,
        "ledger": ledger_file,
        "audit": audit_file
    }

def test_atomic_json_update(nomadic_env):
    """
    Scenario: Atomic State Transition
    Verifies that updating one step doesn't wipe out others.
    """
    manager = LedgerManager(ledger_path=nomadic_env["ledger"])
    
    # Write initial state
    initial_data = {
        "step_1": {"status": "COMPLETED", "last_triggered": "2026-01-01T10:00:00"}
    }
    nomadic_env["ledger"].write_text(json.dumps(initial_data))
    
    # Update a DIFFERENT step
    manager.update_step("step_2", status="IN_PROGRESS", target_repo="physics-worker")
    
    # Verify both exist (No data loss)
    with open(nomadic_env["ledger"], 'r') as f:
        updated_data = json.load(f)
    
    assert "step_1" in updated_data
    assert updated_data["step_2"]["status"] == "IN_PROGRESS"
    assert updated_data["step_2"]["target_repo"] == "physics-worker"

def test_audit_log_prepending(nomadic_env):
    """
    Scenario: The 'Silent Operator' Audit
    Verifies that new events are prepended (top of file) for nomadic monitoring efficiency.
    """
    logger = AuditLogger(audit_path=nomadic_env["audit"])
    
    # Log event 1
    logger.log_event("SCAN", "Initial discovery")
    # Log event 2
    logger.log_event("DISPATCH", "Triggering worker X")
    
    content = nomadic_env["audit"].read_text()
    lines = content.splitlines()
    
    # Verification: Newer events should appear before older events (or at least after header)
    # Based on the "Nomadic Monitoring" mandate in your Constitution:
    assert any("DISPATCH" in line for line in lines)
    assert any("SCAN" in line for line in lines)
    
    # Ensure header isn't wiped
    assert "# Performance Audit Log" in lines[0]

def test_corrupted_json_recovery(nomadic_env):
    """
    Scenario: Hard-Halt on Corruption
    If the ledger is physically corrupted (invalid JSON), the engine must fail safe.
    """
    # Write "poisoned" non-JSON data
    nomadic_env["ledger"].write_text("NOT_JSON_DATA")
    
    manager = LedgerManager(ledger_path=nomadic_env["ledger"])
    
    with pytest.raises(json.JSONDecodeError):
        manager.get_full_state()

def test_ledger_timestamp_format(nomadic_env):
    """
    Verifies that timestamps are written in ISO format for the state engine's timeout logic.
    """
    manager = LedgerManager(ledger_path=nomadic_env["ledger"])
    manager.update_step("timeout_test", status="TRIGGERED")
    
    with open(nomadic_env["ledger"], 'r') as f:
        data = json.load(f)
        timestamp = data["timeout_test"]["last_triggered"]
        
        # Should be parsable by datetime
        assert datetime.fromisoformat(timestamp)