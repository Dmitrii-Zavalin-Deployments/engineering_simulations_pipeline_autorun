# tests/helpers/state_engine_dummy.py

import json
import logging
from pathlib import Path
from typing import Tuple

# Internal Core Imports
from src.core.state_engine import OrchestrationState
from src.core.constants import SystemPaths

logger = logging.getLogger("Engine.TestHelper")

class StateEngineDummy:
    """
    Factory to generate real OrchestrationState instances in a temporary filesystem.
    This bypasses mocking in favor of 'Physical Truth' testing.
    """

    @staticmethod
    def create(
        tmp_path: Path, 
        project_id: str = "TEST-PROJECT", 
        manifest_id: str = "MANIFEST-001",
        steps: list = None
    ) -> Tuple[OrchestrationState, Path]:
        """
        Creates a physical nomadic node environment and returns a hydrated OrchestrationState.
        
        Args:
            tmp_path: The pytest tmp_path fixture (temporary directory).
            project_id: Mock project identifier.
            manifest_id: Mock manifest identifier.
            steps: Optional list of pipeline steps to override the default.
        """
        # 1. Define Paths based on SystemPaths Architecture
        config_dir = tmp_path / SystemPaths.CONFIG_DIR
        data_dir = tmp_path / SystemPaths.DATA_DIR
        config_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        # 2. Create the Core Schema (Mandatory Gate for Hydration)
        schema_path = config_dir / "core_schema.json"
        schema_content = {
            "type": "object",
            "properties": {
                "manifest_id": {"type": "string"},
                "project_id": {"type": "string"},
                "pipeline_steps": {"type": "array"}
            },
            "required": ["manifest_id", "project_id", "pipeline_steps"]
        }
        schema_path.write_text(json.dumps(schema_content), encoding="utf-8")

        # 3. Create the Active Disk Config
        config_path = config_dir / SystemPaths.ACTIVE_DISK
        config_content = {
            "project_id": project_id,
            "manifest_url": "https://raw.githubusercontent.com/dummy/manifest.json"
        }
        config_path.write_text(json.dumps(config_content), encoding="utf-8")

        # 4. Define Pipeline Steps (Default if not provided)
        if steps is None:
            steps = [
                {
                    "name": "alpha_solver",
                    "requires": ["input.csv"],
                    "produces": ["output.csv"],
                    "timeout_hours": 6,
                    "target_repo": "nomad/alpha-worker"
                }
            ]

        manifest_data = {
            "manifest_id": manifest_id,
            "project_id": project_id,
            "pipeline_steps": steps
        }

        # 5. Instantiate and Hydrate the Real Class
        # This ensures __slots__ and validation logic are truly executed.
        state = OrchestrationState(str(config_path), str(data_dir))
        state.hydrate_manifest(manifest_data)

        logger.info(f"🛠️  Test Dummy Created: {project_id} | Node: {tmp_path}")
        return state, data_dir