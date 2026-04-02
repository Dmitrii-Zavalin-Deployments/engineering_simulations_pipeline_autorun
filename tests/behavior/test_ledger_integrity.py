# tests/behavior/test_ledger_integrity.py

import pytest
import json
from datetime import datetime, timezone
from pathlib import Path

# SSoT Alignment: Using the verified LedgerManager from your core directory
from src.core.update_ledger import LedgerManager

@pytest.fixture
def nomadic_env(tmp_path):
    """Sets up a temporary workspace for I/O testing."""
    root = tmp_path / "workdir"
    root.mkdir()
    
    # Matching your engine's expected filenames
    ledger_file = root / "orchestration_ledger.json"
    audit_file = root / "performance_audit.md"
    
    # Initialize files as empty/headers
    ledger_file.write_text("{}")
    audit_file.write_text("# Performance Audit Log\n")
    
    return {
        "root": root,
        "ledger": str(ledger_file),
        "audit": str(audit_file)
    }

def test_atomic_json_update(nomadic_env):
    """
    Scenario: Atomic State Transition
    Verifies that updating one step doesn't wipe out existing ledger data.
    Compliance: Rule 1 (Precision Integrity).
    """
    # Initialize with existing data
    initial_data = {
        "step_1": {
            "status": "COMPLETED", 
            "last_triggered": "2026-01-01T10:00:00+00:00",
            "timeout_hours": 2
        }
    }
    Path(nomadic_env["ledger"]).write_text(json.dumps(initial_data))
    
    manager = LedgerManager(ledger_path=nomadic_env["ledger"], log_path=nomadic_env["audit"])
    
    # Update a DIFFERENT step (step_2)
    manager.update_step(
        step_name="step_2", 
        status="IN_PROGRESS", 
        timeout_hours=6
    )
    
    # Verify both exist (No data loss)
    with open(nomadic_env["ledger"], 'r') as f:
        updated_data = json.load(f)
    
    assert "step_1" in updated_data
    assert updated_data["step_2"]["status"] == "IN_PROGRESS"
    # Verify structure matches your update_ledger.py implementation
    assert "last_triggered" in updated_data["step_2"]

def test_audit_log_persistence(nomadic_env):
    """
    Scenario: The 'Silent Operator' Audit
    Verifies that events are written to the markdown audit log for nomadic monitoring.
    """
    manager = LedgerManager(ledger_path=nomadic_env["ledger"], log_path=nomadic_env["audit"])
    
    # In your code, update_step triggers the audit log entry
    manager.update_step("mesh_gen", "DISPATCHED", timeout_hours=2)
    
    content = Path(nomadic_env["audit"]).read_text()
    
    # Verification: Does the markdown log contain the event?
    assert "mesh_gen" in content
    assert "DISPATCHED" in content
    # Ensure the header was preserved
    assert "# Performance Audit Log" in content

def test_corrupted_json_recovery(nomadic_env):
    """
    Scenario: Hard-Halt on Corruption
    If the ledger is physically corrupted, the manager must raise an error to prevent state drift.
    """
    # Write "poisoned" non-JSON data
    Path(nomadic_env["ledger"]).write_text("NOT_JSON_DATA")
    
    manager = LedgerManager(ledger_path=nomadic_env["ledger"], log_path=nomadic_env["audit"])
    
    # Your implementation of _load_ledger() uses json.load(), which raises JSONDecodeError
    with pytest.raises(json.JSONDecodeError):
        manager.update_step("fail_step", "ERROR", 1)

def test_ledger_timestamp_format(nomadic_env):
    """
    Verifies that timestamps are written in ISO format for the state engine's 
    timeout logic (Rule 4 Enforcement).
    """
    manager = LedgerManager(ledger_path=nomadic_env["ledger"], log_path=nomadic_env["audit"])
    manager.update_step("timeout_test", "TRIGGERED", timeout_hours=1)
    
    with open(nomadic_env["ledger"], 'r') as f:
        data = json.load(f)
        timestamp = data["timeout_test"]["last_triggered"]
        
        # Must be parsable by datetime.fromisoformat
        # and contain the 'Z' or offset if using your utcnow logic
        parsed_dt = datetime.fromisoformat(timestamp)
        assert isinstance(parsed_dt, datetime)

def test_ledger_read_write_cycle(nomadic_env):
    """
    Verifies the get_step_status helper correctly interprets the physical ledger.
    """
    manager = LedgerManager(ledger_path=nomadic_env["ledger"], log_path=nomadic_env["audit"])
    
    # Manually inject a state
    test_time = datetime.now(timezone.utc).isoformat()
    state = {"test_step": {"status": "ACTIVE", "last_triggered": test_time}}
    Path(nomadic_env["ledger"]).write_text(json.dumps(state))
    
    # Test retrieval logic
    status = manager.get_step_status("test_step")
    assert status == "ACTIVE"
    
    # Test missing step logic
    assert manager.get_step_status("non_existent_step") is None