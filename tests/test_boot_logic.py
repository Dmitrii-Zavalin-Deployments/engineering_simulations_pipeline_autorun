# tests/test_boot_logic.py

import pytest
import json
from unittest.mock import patch, MagicMock
from src.core.bootloader import Bootloader

def test_bootloader_transformation_gate(tmp_path):
    """
    VERIFICATION: Verify Bootloader can transform local config and remote JSON
    into a functional state object.
    """
    # 1. Setup Mock config/active_disk.json
    config_file = tmp_path / "active_disk.json"
    config_data = {
        "project_id": "navier_stokes_alpha_01",
        "manifest_url": "https://mock-repo/manifest.json"
    }
    config_file.write_text(json.dumps(config_data))
    
    # Setup mock schema path for OrchestrationState
    schema_dir = tmp_path / "config"
    schema_dir.mkdir()
    (schema_dir / "core_schema.json").write_text(json.dumps({
        "type": "object", 
        "required": ["manifest_id", "pipeline_steps"]
    }))

    # 2. Setup Mock remote manifest
    mock_manifest = {
        "manifest_id": "navier_stokes_alpha_test",
        "pipeline_steps": [
            {
                "name": "navier_stokes_execution",
                "target_repo": "Dmitrii-Zavalin-Deployments/navier_stokes_solver",
                "requires": ["fluid_simulation_input.json"],
                "produces": ["navier_stokes_output.zip"]
            }
        ]
    }

    # 3. Execution with Mocked Network
    with patch('src.core.bootloader.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_manifest
        mock_get.return_value = mock_resp
        
        # Patch the internal schema path to point to our temp mock
        with patch('src.core.state_engine.Path', return_value=schema_dir / "core_schema.json"):
            state = Bootloader.mount(str(config_file), str(tmp_path))
            Bootloader.hydrate(state)
        
        # 4. Final Verification
        assert state.project_id == "navier_stokes_alpha_01"
        assert state.manifest_data["manifest_id"] == "navier_stokes_alpha_test"
        assert "navier_stokes_execution" in state.manifest_data["pipeline_steps"][0]["name"]