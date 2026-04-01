# src/core/state_engine.py

import json
import logging
from pathlib import Path
from jsonschema import validate, ValidationError

logger = logging.getLogger("Engine.State")

class OrchestrationState:
    """
    Forensic Artifact Registry.
    Phase C Compliance: Rule 0 (__slots__), Idempotency Contract, and Schema Sovereignty.
    """
    __slots__ = ['project_id', 'manifest_url', 'data_path', 'manifest_data', 'schema_path']

    def __init__(self, config_path: str, data_root: str):
        self.data_path = Path(data_root)
        self.schema_path = Path("config/core_schema.json")
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'r', encoding="utf-8") as f:
                config = json.load(f)
                self.project_id = config['project_id']
                self.manifest_url = config['manifest_url']
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            raise RuntimeError(f"❌ CRITICAL: Mounting Failed. {e}")
        
        self.manifest_data = None

    def hydrate_manifest(self, manifest_json: dict):
        try:
            with open(self.schema_path, 'r', encoding="utf-8") as s:
                schema = json.load(s)
            validate(instance=manifest_json, schema=schema)
            self.manifest_data = manifest_json
            logger.info(f"💿 Registry Hydrated & Validated: [{manifest_json['manifest_id']}]")
        except Exception as e:
            raise RuntimeError(f"❌ CRITICAL: Hard-Halt. Manifest is corrupt. {e}")

    def forensic_artifact_scan(self):
        """
        THE PARALLEL GAP FINDER (DAG Truth):
        Identifies ALL steps whose 'Requires' are met but 'Produces' are missing.
        """
        if not self.manifest_data:
            raise RuntimeError("❌ CRITICAL: Scan attempted without Manifest Hydration.")

        ready_steps = []

        for step in self.manifest_data["pipeline_steps"]:
            # Evidence check on the physical Foundation
            input_evidence = all((self.data_path / f).exists() for f in step['requires'])
            output_missing = any(not (self.data_path / f).exists() for f in step['produces'])

            # SCENARIO: Task is ready for concurrent dispatch
            if input_evidence and output_missing:
                logger.info(f"🔍 Forensic Scan: Ready for Dispatch [{step['name']}]")
                ready_steps.append(step)
                continue 

            # SCENARIO: Task already completed; skip and check next potential branch
            if input_evidence and not output_missing:
                logger.debug(f"Step [{step['name']}] skipped: Artifacts present.")
                continue

            # SCENARIO: Task blocked; do not log to keep diagnostic signals clean
            if not input_evidence:
                continue
        
        return ready_steps if ready_steps else None