# tests/behavior/test_forensic_table.py

import pytest
import json
import logging
from src.core.state_engine import OrchestrationState

logger = logging.getLogger(__name__)

@pytest.fixture
def state_manager(tmp_path):
    """Setup a mock environment for Truth Table verification."""
    config = tmp_path / "active_disk.json"
    config.write_text(json.dumps({"project_id": "test_proj", "manifest_url": "http://mock.io"}))
    
    schema_path = tmp_path / "config"
    schema_path.mkdir()
    (schema_path / "core_schema.json").write_text(json.dumps({"type": "object"}))
    
    manifest = {
        "manifest_id": "test_v1",
        "pipeline_steps": [
            {
                "name": "geometry_generator",
                "requires": [],
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
    targets = state_manager.forensic_artifact_scan({})
    target = targets[0] if targets else None
    assert target['name'] == "geometry_generator"

def test_scenario_geometry_present(state_manager):
    """TABLE ROW 2: geometry.msh present -> Trigger Physics Step."""
    (state_manager.data_path / "geometry.msh").write_text("mesh_data")
    targets = state_manager.forensic_artifact_scan({})
    target = targets[0] if targets else None
    assert target['name'] == "navier_stokes_solver"

def test_scenario_results_present(state_manager):
    """TABLE ROW 3: results.zip present -> Halt (Cycle Complete)."""
    (state_manager.data_path / "geometry.msh").write_text("mesh_data")
    (state_manager.data_path / "results.zip").write_text("result_data")
    targets = state_manager.forensic_artifact_scan({})
    assert targets is None