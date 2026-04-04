# tests/helpers/state_engine_dummy.py

import json
from pathlib import Path
from typing import Tuple
from src.core.constants import SystemPaths
from src.core.state_engine import OrchestrationState

class StateEngineDummy:
    """
    Test Factory for the Nomadic Engine.
    Responsibility: Creates physical mock environments for Integration Testing.
    Compliance: Rule 4 (Zero-Default) & Phase C (Atomic Persistence).
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
        Satisfies the OrchestrationState signature and enforces path-locality for tests.
        """
        # 1. Define Paths based on SystemPaths (Rule 4)
        # We use tmp_path as the 'Physical Node Root' for this test execution
        config_dir = tmp_path / SystemPaths.CONFIG_DIR
        schema_dir = tmp_path / SystemPaths.SCHEMA_DIR
        data_dir = tmp_path / SystemPaths.DATA_DIR
        
        for directory in [config_dir, schema_dir, data_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Define the ledger path inside the mock config directory
        ledger_path = config_dir / SystemPaths.LEDGER

        # 2. Create the Manifest Schema (Rule 4 Compliance)
        # This prevents FileNotFoundError during hydration
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
        
        # 4. Create the Active Disk Config
        config_path = config_dir / SystemPaths.ACTIVE_DISK
        config_content = {
            "project_id": project_id,
            "manifest_url": "https://raw.githubusercontent.com/dummy/manifest.json"
        }
        config_path.write_text(json.dumps(config_content), encoding="utf-8")
        
        # 5. Define Pipeline Steps
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

        # 6. Instantiate the Real Class with Test-Local Paths
        # This overrides the production default 'schema/' with the temp one
        state = OrchestrationState()
        state.config_path = str(config_path)
        state.data_root = str(data_dir)
        state.ledger_path = str(ledger_path)
        state.schema_path = str(manifest_schema_path) # Critical fix: point directly to the temp schema
        
        # 7. Manual hydration for test isolation
        # This will now succeed because state.schema_path exists on disk
        state.hydrate_manifest({
            "manifest_id": manifest_id,
            "project_id": project_id,
            "pipeline_steps": steps
        })
        
        return state, data_dir