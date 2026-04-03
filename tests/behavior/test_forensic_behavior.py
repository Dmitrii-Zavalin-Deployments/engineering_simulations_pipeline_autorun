import pytest
from datetime import datetime, timedelta, timezone

# Internal Core Imports
from src.core.constants import OrchestrationStatus
from tests.helpers.state_engine_dummy import StateEngineDummy

@pytest.fixture
def behavior_env(tmp_path):
    """
    Sets up a 2-step pipeline for behavior testing.
    Step 1 -> Produces f1.out
    Step 2 -> Requires f1.out, Produces f2.out
    """
    steps = [
        {
            "name": "step_1", 
            "target_repo": "repo/s1", 
            "timeout_hours": 2, 
            "requires": [], 
            "produces": ["f1.out"]
        },
        {
            "name": "step_2", 
            "target_repo": "repo/s2", 
            "timeout_hours": 6, 
            "requires": ["f1.out"], 
            "produces": ["f2.out"]
        }
    ]
    state, data_path = StateEngineDummy.create(tmp_path, steps=steps)
    return state, data_path

def test_scenario_in_flight_lock_retention(behavior_env):
    """
    Scenario: Valid IN_PROGRESS status must prevent re-dispatch.
    Logic: If time < timeout and no output exists, stay IN_PROGRESS.
    """
    state, data_path = behavior_env
    
    # Arrange: Step 2 requires f1.out (physically present)
    (data_path / "f1.out").touch()
    
    # Step 2 started 10 minutes ago (Timeout is 6 hours)
    recent_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    ledger = {
        "step_2": {
            "status": OrchestrationStatus.IN_PROGRESS.value, 
            "last_triggered": recent_time, 
            "timeout_hours": 6
        }
    }
    
    # Act
    healed_ledger = state.reconcile_and_heal(ledger)
    ready_steps = state.get_ready_steps(healed_ledger)
    
    # Assert: Status remains IN_PROGRESS, so get_ready_steps returns None
    assert healed_ledger["step_2"]["status"] == OrchestrationStatus.IN_PROGRESS.value
    assert ready_steps is None

def test_scenario_timeout_to_failed_to_pending(behavior_env):
    """
    Scenario: Execution Timeout Recovery
    Logic: IN_PROGRESS + Time > Timeout -> FAILED -> PENDING (since inputs exist)
    """
    state, data_path = behavior_env
    
    # Step 1 has no requirements, so inputs_exist is always True.
    # Step 1 started 5 hours ago (Timeout is 2 hours)
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    ledger = {
        "step_1": {
            "status": OrchestrationStatus.IN_PROGRESS.value, 
            "last_triggered": stale_time, 
            "timeout_hours": 2
        }
    }
    
    # Act
    healed_ledger = state.reconcile_and_heal(ledger)
    ready_steps = state.get_ready_steps(healed_ledger)
    
    # Assert: Matrix flips: IN_PROGRESS -> FAILED -> PENDING
    assert healed_ledger["step_1"]["status"] == OrchestrationStatus.PENDING.value
    assert ready_steps[0]["name"] == "step_1"

def test_scenario_liar_ledger_healing(behavior_env):
    """
    Scenario: The 'Liar Ledger' (COMPLETED status but file missing)
    Logic: COMPLETED + File Missing -> WAITING -> (If inputs exist) -> PENDING
    """
    state, data_path = behavior_env
    
    # Arrange: Ledger says step_1 is done, but data_path is empty (f1.out missing)
    ledger = {
        "step_1": {
            "status": OrchestrationStatus.COMPLETED.value,
            "last_triggered": "2026-01-01T00:00:00+00:00"
        }
    }
    
    # Act
    healed_ledger = state.reconcile_and_heal(ledger)
    ready_steps = state.get_ready_steps(healed_ledger)
    
    # Assert: Matrix detected the missing file and reset the task to PENDING
    # (Since step_1 has no requirements, it skips WAITING and goes straight to PENDING)
    assert healed_ledger["step_1"]["status"] == OrchestrationStatus.PENDING.value
    assert ready_steps[0]["name"] == "step_1"

def test_scenario_blocked_dependency(behavior_env):
    """
    Scenario: Dependency Blocking
    Logic: Step 2 cannot go PENDING if Step 1 hasn't produced f1.out.
    """
    state, data_path = behavior_env
    
    # Arrange: Step 1 is WAITING, Step 2 is WAITING. No files exist.
    ledger = {
        "step_1": {"status": OrchestrationStatus.WAITING.value},
        "step_2": {"status": OrchestrationStatus.WAITING.value}
    }
    
    # Act
    healed_ledger = state.reconcile_and_heal(ledger)
    ready_steps = state.get_ready_steps(healed_ledger)
    
    # Assert: Only Step 1 is PENDING (no requirements). 
    # Step 2 stays WAITING because f1.out is missing.
    assert healed_ledger["step_1"]["status"] == OrchestrationStatus.PENDING.value
    assert healed_ledger["step_2"]["status"] == OrchestrationStatus.WAITING.value
    assert len(ready_steps) == 1
    assert ready_steps[0]["name"] == "step_1"