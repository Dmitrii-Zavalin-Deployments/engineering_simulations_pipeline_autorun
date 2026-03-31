# src/core/state_engine.py

import json
import logging
from pathlib import Path

# Configure Logger for State Registry Traceability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("Engine.State")

class OrchestrationState:
    """
    Forensic Artifact Registry.
    Phase C Compliance: Rule 0 (__slots__) & Idempotency Contract.
    """
    __slots__ = ['project_id', 'manifest_url', 'data_path', 'manifest_data']

    def __init__(self, config_path: str, data_root: str):
        self.data_path = Path(data_root)
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
        """
        # Rule 4: Explicit Key Validation (Zero-Default Policy)
        required = ["manifest_id", "pipeline_steps"]
        for key in required:
            if key not in manifest_json:
                logger.error(f"Manifest malformed. Missing key: '{key}'")
                raise KeyError(f"❌ CRITICAL: Manifest malformed. Missing: '{key}'")
        
        self.manifest_data = manifest_json
        logger.info(f"💿 Registry Hydrated: [{manifest_json['manifest_id']}]")

    def forensic_artifact_scan(self):
        """
        IDEMPOTENCY CONTRACT:
        Filesystem truth is absolute. Resumes by identifying the first
        'Requirement' that lacks a 'Production' artifact.
        
        Rule 4 Guard: Explicit failure if scan is attempted before hydration.
        """
        if not self.manifest_data:
            logger.critical("Engine logic breach. Scan attempted without Manifest Hydration.")
            raise RuntimeError("❌ CRITICAL: Scan attempted without Manifest Hydration.")

        for step in self.manifest_data["pipeline_steps"]:
            # Rule: Evidence-Based Verification
            # Check if all inputs (Requires) exist on disk
            input_evidence = all((self.data_path / f).exists() for f in step['requires'])
            
            # Check if any outputs (Produces) are missing
            output_missing = any(not (self.data_path / f).exists() for f in step['produces'])

            # The 'Gap' is found when inputs exist but outputs do not.
            if input_evidence and output_missing:
                logger.info(f"🔍 Forensic Scan: Gate OPEN for step [{step['name']}]")
                return step
        
        logger.info("✅ Forensic Scan: Pipeline saturated. No gaps detected.")
        return None