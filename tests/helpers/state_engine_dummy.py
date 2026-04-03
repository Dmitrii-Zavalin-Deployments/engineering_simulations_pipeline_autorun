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
    Updated for Phase C Schema Sovereignty and Directory Relocation.
    """

    @staticmethod
    def create(
        tmp_path: Path, 
        project_id: str = "TEST-PROJECT", 
        manifest_id: str = "MANIFEST-001",
        steps: list = None
    ) -> Tuple[OrchestrationState, Path]:
        """
        Creates a physical nomadic node environment including the /schema directory.
        """
        # 1. Define Paths based on SystemPaths (Rule 4)
        config_dir = tmp_path / SystemPaths.CONFIG_DIR
        schema_dir = tmp_path / SystemPaths.SCHEMA_DIR
        data_dir = tmp_path / SystemPaths.DATA_DIR
        
        for directory in [config_dir, schema_dir, data_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # 2. Create the Manifest Schema (Moved to /schema)
        manifest_schema_path = schema_dir / SystemPaths.MANIFEST_SCHEMA
        manifest_schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "manifest_id": {"type": "string"},
                "project_id": {"type": "string"},
                "pipeline_steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "target_repo": {"type": "string"},
                            "timeout_hours": {"type": "integer"},
                            "requires": {"type": "array", "items": {"type": "string"}},
                            "produces": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["name", "target_repo", "requires", "produces"]
                    }
                }
            },
            "required": ["manifest_id", "project_id", "pipeline_steps"]
        }
        manifest_schema_path.write_text(json.dumps(manifest_schema_content), encoding="utf-8")

        # 3. Create the Active Disk Schema
        active_disk_schema_path = schema_dir / SystemPaths.ACTIVE_DISK_SCHEMA
        active_disk_schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "manifest_url": {"type": "string"}
            },
            "required": ["project_id", "manifest_url"]
        }
        active_disk_schema_path.write_text(json.dumps(active_disk_schema_content), encoding="utf-8")

        # 4. Create the Active Disk Config (Rule 4: Direct Key Access)
        config_path = config_dir / SystemPaths.ACTIVE_DISK
        config_content = {
            "project_id": project_id,
            "manifest_url": "https://raw.githubusercontent.com/dummy/manifest.json"
        }
        config_path.write_text(json.dumps(config_content), encoding="utf-8")

        # 5. Define Pipeline Steps (Rule 4: No silent defaults)
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

        # 6. Instantiate and Hydrate the Real Class
        # We pass strings of the paths to mimic the real entry point.
        state = OrchestrationState(str(config_path), str(data_dir))
        state.hydrate_manifest(manifest_data)

        logger.info(f"🛠️  Test Dummy Created: {project_id} | Node: {tmp_path}")
        return state, data_dir