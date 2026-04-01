# src/core/state_engine.py

import json
import logging
from pathlib import Path
from jsonschema import validate, ValidationError

# Configure Logger for State Registry Traceability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
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
        
        # Rule: The Machine Must Clean Itself - ensure path exists but stays stateless
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # 1. Mounting Protocol (Single-Slot Rule)
        try:
            with open(config_path, 'r', encoding="utf-8") as f:
                config = json.load(f)
                # Rule 4: Explicit or Error - No .get() defaults
                self.project_id = config['project_id']
                self.manifest_url = config['manifest_url']
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            logger.critical(f"Mounting Failed. active_disk.json invalid or missing: {e}")
            raise RuntimeError(f"❌ CRITICAL: Mounting Failed. {e}")
        
        self.manifest_data = None

    def hydrate_manifest(self, manifest_json: dict):
        """
        Runtime Hydration: Schema Sovereignty check before execution.
        Rule: A 'corrupt disk' (Schema Violation) results in an immediate Hard-Halt.
        """
        try:
            with open(self.schema_path, 'r', encoding="utf-8") as s:
                schema = json.load(s)
            
            validate(instance=manifest_json, schema=schema)
            
            self.manifest_data = manifest_json
            logger.info(f"💿 Registry Hydrated & Validated: [{manifest_json['manifest_id']}]")
            
        except FileNotFoundError:
            logger.error("Core Schema missing at config/core_schema.json.")
            raise RuntimeError("❌ CRITICAL: Schema Missing. Validation aborted.")
        except ValidationError as e:
            logger.critical(f"Manifest Schema Violation: {e.message}")
            raise RuntimeError(f"❌ CRITICAL: Hard-Halt. Manifest is corrupt. {e.message}")

    def forensic_artifact_scan(self):
        """
        THE GAP FINDER LOGIC (Sequential Truth):
        Identifies the first step that has its 'Requires' met but its 'Produces' missing.
        It is blind to physics, only verifying physical existence.
        """
        if not self.manifest_data:
            logger.critical("Engine logic breach. Scan attempted without Manifest Hydration.")
            raise RuntimeError("❌ CRITICAL: Scan attempted without Manifest Hydration.")

        for step in self.manifest_data["pipeline_steps"]:
            # Rule: Evidence-Based Verification
            # Check if all inputs (Requires) exist on disk
            input_evidence = all((self.data_path / f).exists() for f in step['requires'])
            
            # Check if any outputs (Produces) are missing
            # Using any() ensures that if a step is partially failed, it restarts.
            output_missing = any(not (self.data_path / f).exists() for f in step['produces'])

            # The 'Gate' opens when inputs exist but outputs do not.
            if input_evidence and output_missing:
                logger.info(f"🔍 Forensic Scan: Gate OPEN for step [{step['name']}]")
                return step
            
            # If inputs are missing, the pipeline is blocked at this stage.
            if not input_evidence:
                logger.debug(f"Step [{step['name']}] blocked: Missing required input artifacts.")
                break
        
        logger.info("✅ Forensic Scan: Pipeline saturated. No gaps detected.")
        return None