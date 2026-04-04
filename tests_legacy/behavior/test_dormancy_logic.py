# tests/behavior/test_dormancy_logic.py

import pytest
import os
from pathlib import Path
from src.core.update_ledger import LedgerManager
from src.core.constants import OrchestrationStatus, SystemPaths

## ==========================================================
## BEHAVIOR TEST: DORMANCY ORCHESTRATION (Rule 1)
## ==========================================================

@pytest.fixture
def manager(tmp_path):
    """
    Provides a LedgerManager instance pointing to a temporary test directory.
    Aligns with SystemPaths and the nomadic 'Asset-Only' model.
    """
    # 1. Setup local testing-input-output directory
    test_root = tmp_path / "data" / "testing-input-output"
    test_root.mkdir(parents=True, exist_ok=True)
    
    # 2. Setup config dir for the flag
    (tmp_path / SystemPaths.CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    
    # 3. Use Monkeypatch to force SystemPaths to look at our tmp_path
    # This ensures the LedgerManager writes to the temp directory, not your real project root.
    os.chdir(tmp_path)
    
    return LedgerManager(log_path="performance_audit.md")

def test_dormancy_scenario_active_incomplete(manager, tmp_path):
    """
    SCENARIO: One step is COMPLETED, one is IN_PROGRESS.
    EXPECTED: Flag must be STATUS: ACTIVE.
    """
    ledger_steps = {
        "step_alpha": {"status": OrchestrationStatus.COMPLETED.value},
        "step_beta": {"status": OrchestrationStatus.IN_PROGRESS.value}
    }
    
    status = manager.evaluate_dormancy_state(ledger_steps)
    
    assert status == "STATUS: ACTIVE"
    flag_content = Path(manager.flag_path).read_text()
    assert "ACTIVE" in flag_content

def test_dormancy_scenario_saturation_hibernation(manager, tmp_path):
    """
    SCENARIO: All steps in the ledger are COMPLETED.
    EXPECTED: Flag must be STATUS: DORMANT (Hibernation Trigger).
    """
    ledger_steps = {
        "navier_stokes_execution": {"status": OrchestrationStatus.COMPLETED.value},
        "thermal_analysis": {"status": OrchestrationStatus.COMPLETED.value}
    }
    
    status = manager.evaluate_dormancy_state(ledger_steps)
    
    assert status == "STATUS: DORMANT"
    flag_content = Path(manager.flag_path).read_text()
    assert "DORMANT" in flag_content
    
    # Verify Rule 5: Operational Hygiene (Audit Record)
    audit_log = Path(manager.log_path).read_text()
    assert "DORMANCY_LOCK" in audit_log
    assert "hibernation" in audit_log

def test_dormancy_scenario_empty_ledger(manager, tmp_path):
    """
    SCENARIO: Ledger is empty (New Project).
    EXPECTED: Flag must be STATUS: ACTIVE to allow the first pulse.
    """
    status = manager.evaluate_dormancy_state({})
    
    assert status == "STATUS: ACTIVE"

def test_dormancy_scenario_regression_to_active(manager, tmp_path):
    """
    SCENARIO: System was DORMANT, but a step is reset to WAITING (Artifact Drift).
    EXPECTED: Flag must flip back to STATUS: ACTIVE.
    """
    # 1. Pre-set to DORMANT
    Path(manager.flag_path).parent.mkdir(parents=True, exist_ok=True)
    Path(manager.flag_path).write_text("STATUS: DORMANT")
    
    # 2. Simulate Drift (Step is no longer completed)
    ledger_steps = {
        "simulation_01": {"status": OrchestrationStatus.WAITING.value}
    }
    
    status = manager.evaluate_dormancy_state(ledger_steps)
    
    assert status == "STATUS: ACTIVE"
    assert "ACTIVE" in Path(manager.flag_path).read_text()

def test_dormancy_scenario_rule_4_failure(manager):
    """
    SCENARIO: Ledger entry is corrupted (missing status key).
    EXPECTED: Hard-Halt (KeyError) per Rule 4.
    """
    corrupt_steps = {
        "broken_step": {"not_a_status_key": "oops"}
    }
    
    with pytest.raises(KeyError):
        manager.evaluate_dormancy_state(corrupt_steps)