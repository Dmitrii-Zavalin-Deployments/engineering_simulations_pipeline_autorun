# tests/behavior/test_forensic_table.py

import pytest
from src.core.constants import OrchestrationStatus
from tests.helpers.state_engine_dummy import StateEngineDummy

@pytest.fixture
def table_env(tmp_path):
    """
    Sets up the Physics Truth Table environment.
    Step 1: Geometry Generator (No requirements)
    Step 2: Navier Stokes Solver (Requires Geometry)
    """
    steps = [
        {
            "name": "geometry_generator",
            "requires": [],
            "produces": ["geometry.msh"],
            "target_repo": "org/geom-gen",
            "timeout_hours": 2
        },
        {
            "name": "navier_stokes_solver",
            "requires": ["geometry.msh"],
            "produces": ["results.zip"],
            "target_repo": "org/ns-solver",
            "timeout_hours": 6
        }
    ]
    state, data_path = StateEngineDummy.create(tmp_path, steps=steps)
    return state, data_path

def test_table_row_1_empty_vault(table_env):
    """TRUTH TABLE: Vault Empty -> Identify Initial Step."""
    state, data_path = table_env
    
    # 1. Start with an empty ledger
    ledger = {} 
    
    # 2. Heal and Identify
    healed = state.reconcile_and_heal(ledger)
    ready = state.get_ready_steps(healed)
    
    # 3. Assert: Geometry Generator should be PENDING
    assert healed["geometry_generator"]["status"] == OrchestrationStatus.PENDING.value
    assert ready[0]["name"] == "geometry_generator"
    assert len(ready) == 1

def test_table_row_2_geometry_present(table_env):
    """TRUTH TABLE: Geometry Present -> Identify Physics Step."""
    state, data_path = table_env
    
    # 1. Arrange: Physically place the mesh file
    (data_path / "geometry.msh").touch()
    
    # 2. Heal and Identify
    healed = state.reconcile_and_heal({})
    ready = state.get_ready_steps(healed)
    
    # 3. Assert: Step 1 is COMPLETED, Step 2 is PENDING
    assert healed["geometry_generator"]["status"] == OrchestrationStatus.COMPLETED.value
    assert healed["navier_stokes_solver"]["status"] == OrchestrationStatus.PENDING.value
    assert ready[0]["name"] == "navier_stokes_solver"

def test_table_row_3_full_saturation(table_env):
    """TRUTH TABLE: All Artifacts Present -> Saturated (No Ready Steps)."""
    state, data_path = table_env
    
    # 1. Arrange: Place all outputs
    (data_path / "geometry.msh").touch()
    (data_path / "results.zip").touch()
    
    # 2. Heal and Identify
    healed = state.reconcile_and_heal({})
    ready = state.get_ready_steps(healed)
    
    # 3. Assert: Both COMPLETED, nothing ready
    assert healed["geometry_generator"]["status"] == OrchestrationStatus.COMPLETED.value
    assert healed["navier_stokes_solver"]["status"] == OrchestrationStatus.COMPLETED.value
    assert ready is None

def test_table_row_4_partial_drift(table_env):
    """TRUTH TABLE: Results exist but Geometry deleted -> Re-verify/Heal."""
    state, data_path = table_env
    
    # 1. Arrange: Ledger says both done, but geometry.msh was deleted
    (data_path / "results.zip").touch()
    # (geometry.msh is missing)
    
    ledger = {
        "geometry_generator": {"status": OrchestrationStatus.COMPLETED.value},
        "navier_stokes_solver": {"status": OrchestrationStatus.COMPLETED.value}
    }
    
    # 2. Heal
    healed = state.reconcile_and_heal(ledger)
    
    # 3. Assert: 
    # Geometry generator flips back to PENDING (it has no requirements and output is missing)
    # Solver stays COMPLETED (its output results.zip is physically there)
    assert healed["geometry_generator"]["status"] == OrchestrationStatus.PENDING.value
    assert healed["navier_stokes_solver"]["status"] == OrchestrationStatus.COMPLETED.value