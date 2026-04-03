# tests/core/test_future_proof.py

import pytest
import json
from src.core.constants import OrchestrationStatus
from tests.helpers.state_engine_dummy import StateEngineDummy

@pytest.fixture
def future_proof_env(tmp_path):
    """
    Sets up an Agnostic Engine instance with a hypothetical 'Future Project'.
    This project uses 'Quantum' terminology to prove the engine is domain-blind.
    """
    future_steps = [
        {
            "name": "quantum_init",
            "requires": ["initial_seed.dat"],
            "produces": ["quantum_state.bin"],
            "target_repo": "org/quantum-worker",
            "timeout_hours": 1
        }
    ]
    
    # Use the dummy factory to create a 'Future Project X' environment
    state, data_path = StateEngineDummy.create(
        tmp_path, 
        project_id="FUTURE-PROJECT-X", 
        steps=future_steps
    )
    return state, data_path

def test_agnostic_logic_execution(future_proof_env):
    """
    SCENARIO: The 'Agnostic' Test.
    The Engine must identify 'quantum_init' purely based on the presence 
    of 'initial_seed.dat', without any hardcoded knowledge of the project.
    """
    state, data_path = future_proof_env
    
    # 1. Arrange: Provide the physical requirement for the future step
    (data_path / "initial_seed.dat").write_text("QUANTUM_ENTROPY_0101", encoding="utf-8")
    
    # 2. Act: Reconcile (Heal) and Get Ready Steps
    # We start with an empty ledger to force a forensic reconstruction
    healed_ledger = state.reconcile_and_heal({})
    ready_steps = state.get_ready_steps(healed_ledger)
    
    # 3. Assert: Logic-Driven Identification
    assert ready_steps is not None
    assert ready_steps[0]["name"] == "quantum_init"
    assert ready_steps[0]["target_repo"] == "org/quantum-worker"
    
    # Verify the status is PENDING (Ready for dispatch)
    assert healed_ledger["quantum_init"]["status"] == OrchestrationStatus.PENDING.value

def test_sync_failure_hard_halt(future_proof_env):
    """
    SCENARIO: Conflict Simulation (Broken Sync / Missing Artifact).
    Rule 4 Compliance: If a file is missing (e.g., Dropbox sync lag),
    the Engine must stay in WAITING/FAILED rather than moving forward.
    """
    state, data_path = future_proof_env
    
    # 1. Arrange: The directory is empty. 'initial_seed.dat' DOES NOT EXIST.
    # Ledger claims it should be ready.
    ledger = {"quantum_init": {"status": OrchestrationStatus.WAITING.value}}
    
    # 2. Act: Reconcile
    healed_ledger = state.reconcile_and_heal(ledger)
    ready_steps = state.get_ready_steps(healed_ledger)
    
    # 3. Assert: Physical Truth Prevails
    # Even though it's WAITING, it cannot go PENDING because the input is missing.
    assert healed_ledger["quantum_init"]["status"] == OrchestrationStatus.WAITING.value
    assert ready_steps is None
    
def test_future_saturation_check(future_proof_env):
    """
    SCENARIO: Future Saturation.
    Verifies that even a 'Quantum' project correctly identifies completion
    when the final artifact is detected.
    """
    state, data_path = future_proof_env
    
    # 1. Arrange: Place the 'future' output file
    (data_path / "quantum_state.bin").write_text("STABLE_WAVEFUNCTION", encoding="utf-8")
    
    # 2. Act
    healed_ledger = state.reconcile_and_heal({})
    ready_steps = state.get_ready_steps(healed_ledger)
    
    # 3. Assert: Saturation Reached
    assert healed_ledger["quantum_init"]["status"] == OrchestrationStatus.COMPLETED.value
    assert ready_steps is None