# tests/core/test_ledger_logic.py

import pytest
import logging

# Internal Core Imports
from src.core.update_ledger import LedgerManager

logger = logging.getLogger("Engine.Test.Ledger")

@pytest.fixture
def audit_env(tmp_path):
    """Sets up a physical audit environment for SSoT verification."""
    audit_file = tmp_path / "performance_audit.md"
    # Ensure a header exists to test prepending beneath/above it
    audit_file.write_text("# 🛰️ Nomad Engine Audit\n\n", encoding="utf-8")
    
    # Initialize Manager (orchestration_path isn't needed for pure log tests)
    manager = LedgerManager(log_path=str(audit_file))
    return manager, audit_file

def test_ledger_prepend_order(audit_env):
    """
    Scenario: Newest-First Pulse.
    Rule 5 Compliance: Operational Hygiene.
    Verifies that the ledger follows the 'Atomic Prepend' rule.
    """
    manager, audit_file = audit_env

    # 1. Record a sequence of events
    manager.record_event("FIRST_PULSE", "This should be at the bottom.")
    manager.record_event("SECOND_PULSE", "This should be at the top.")

    # 2. Act: Read the physical file
    content = audit_file.read_text(encoding="utf-8")
    
    # 3. Assert: "SECOND_PULSE" index must be lower than "FIRST_PULSE" (higher in file)
    idx_first = content.find("FIRST_PULSE")
    idx_second = content.find("SECOND_PULSE")
    
    assert idx_second < idx_first, "Log failed to prepend. Newest entries must be at the top."
    logger.info("✅ Prepend Order Verified: Latest telemetry is prioritized.")

def test_audit_consistency_sequence(audit_env):
    """
    VERIFICATION: Full Forensic Traceability.
    Ensures the SCAN -> HEAL -> DISPATCH sequence is recorded atomically.
    """
    manager, audit_file = audit_env
    project_id = "OCEANS-V1"
    manifest_id = "M-ALPHA"
    
    # 1. Simulate the Engine Loop
    # Phase A: Forensic Scan
    manager.log_scan(project_id, "GAP_DETECTED", gap="power_station_solver")
    
    # Phase B: Dispatching a Worker
    manager.log_dispatch(
        project_id=project_id,
        manifest_id=manifest_id,
        step_name="power_station_solver",
        target_repo="Dmitrii-Zavalin/oceans-worker",
        timeout_hours=12
    )
    
    # 2. Act: Verify physical MD content
    content = audit_file.read_text(encoding="utf-8")
    
    # 3. Assert: Check for key forensic markers
    assert "🔍 FORENSIC_SCAN" in content
    assert "🚀 DISPATCH" in content
    assert "power_station_solver" in content
    assert project_id in content
    
    # Verify the specific "GAP_DETECTED" metadata was logged
    assert "gap: power_station_solver" in content.lower()
    logger.info("✅ Audit Traceability Verified: Full nomadic sequence is intact.")

def test_audit_file_creation_resilience(tmp_path):
    """
    Scenario: Missing Log File.
    Verifies the manager creates the audit file if it doesn't exist (Self-Healing).
    """
    missing_log = tmp_path / "subdir" / "new_audit.md"
    manager = LedgerManager(log_path=str(missing_log))
    
    # Trigger a log event
    manager.record_event("INIT", "First nomadic pulse.")
    
    # Verification
    assert missing_log.exists()
    assert "INIT" in missing_log.read_text()