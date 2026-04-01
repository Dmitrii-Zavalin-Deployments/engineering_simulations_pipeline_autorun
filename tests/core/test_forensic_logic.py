# tests/core/test_forensic_logic.py

import pytest
import json
import logging
from src.core.state_engine import OrchestrationState

# Standard logger setup for forensic tests
logger = logging.getLogger(__name__)

@pytest.fixture
def state_manager(tmp_path):
    """Setup a mock environment with a 2-step manifest."""
    config = tmp_path / "active_disk.json"
    config.write_text(json.dumps({"project_id": "test_proj", "manifest_url": "http://mock.io"}))
    
    # Mock Schema for hydration
    schema_path = tmp_path / "config"
    schema_path.mkdir()
    (schema_path / "core_schema.json").write_text(json.dumps({"type": "object"}))
    
    # Define the Table Scenario Pipeline
    manifest = {
        "manifest_id": "test_v1",
        "pipeline_steps": [
            {
                "name": "geometry_generator",
                "requires": [], # Initial step: no requirement
                "produces": ["geometry.msh"],
                "target_repo": "org/geom-gen"
            },
            {
                "name": "navier_stokes_solver",
                "requires": ["geometry.msh"],
                "produces": ["results.zip"],
                "target_repo": "org/ns-solver"
            }
        ]
    }
    
    state = OrchestrationState(str(config), str(tmp_path / "data"))
    state.schema_path = schema_path / "core_schema.json"
    state.hydrate_manifest(manifest)
    return state

def test_scenario_empty_folder(state_manager):
    """TABLE ROW 1: Empty Folder -> Trigger Initial Step."""
    logger.info("Running: TABLE ROW 1 (Empty Folder)")
    targets = state_manager.forensic_artifact_scan()
    target = targets[0] if targets else None
    assert target['name'] == "geometry_generator"
    assert target['target_repo'] == "org/geom-gen"

def test_scenario_geometry_present(state_manager):
    """TABLE ROW 2: geometry.msh present -> Trigger Physics Step."""
    logger.info("Running: TABLE ROW 2 (Geometry Present)")
    (state_manager.data_path / "geometry.msh").write_text("mesh_data")
    
    targets = state_manager.forensic_artifact_scan()
    target = targets[0] if targets else None
    assert target['name'] == "navier_stokes_solver"
    assert target['target_repo'] == "org/ns-solver"

def test_scenario_results_present(state_manager):
    """TABLE ROW 3: results.zip present -> Halt (Cycle Complete)."""
    logger.info("Running: TABLE ROW 3 (Results Present)")
    (state_manager.data_path / "geometry.msh").write_text("mesh_data")
    (state_manager.data_path / "results.zip").write_text("result_data")
    
    targets = state_manager.forensic_artifact_scan()
    target = targets[0] if targets else None
    assert target is None
    logger.info("✅ Saturation Verified: Engine stood down as expected.")