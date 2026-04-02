# src/core/state_engine.py

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from jsonschema import validate

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
        if not self.data_path.exists():
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

    def _is_job_stale(self, job_name: str, ledger: dict) -> bool:
        """
        Internal Logic Gate: Determines if a job is truly 'In-Flight'.
        Phase C Compliance: Rule 4 (Zero-Default). 
        Throws KeyError if timeout_hours is missing from the ledger.
        """
        if job_name not in ledger:
            return True # Not in flight, proceed to dispatch

        job_data = ledger[job_name]
        
        # Rule 4: No fallback '6'. We fetch the key directly.
        # If the key is missing, Python raises a KeyError, triggering a Hard-Halt.
        try:
            timeout_h = job_data["timeout_hours"]
            last_trigger_str = job_data["last_triggered"]
        except KeyError as e:
            logger.critical(f"Protocol Breach: Ledger entry for [{job_name}] is missing mandatory key {e}")
            raise RuntimeError(f"❌ CRITICAL: Data integrity failure in Orchestration Ledger. Missing {e}")

        last_trigger = datetime.fromisoformat(last_trigger_str)
        
        # Comparison logic remains mathematical and strict
        is_stale = datetime.now(timezone.utc) > (last_trigger + timedelta(hours=timeout_h))
        
        if is_stale:
            logger.warning(f"⚠️ Job [{job_name}] has exceeded its {timeout_h}h window. Marking as STALE.")
            
        return is_stale

    def forensic_artifact_scan(self, orchestration_ledger: dict):
        """
        THE PARALLEL GAP FINDER (DAG Truth):
        Identifies steps where 'Requires' are met, 'Produces' are missing, 
        AND no valid 'In-Flight' lock exists in the orchestration ledger.
        """
        if not self.manifest_data:
            raise RuntimeError("❌ CRITICAL: Scan attempted without Manifest Hydration.")

        ready_steps = []

        for step in self.manifest_data["pipeline_steps"]:
            # 1. Evidence check on the physical Foundation
            input_evidence = all((self.data_path / f).exists() for f in step['requires'])
            output_missing = any(not (self.data_path / f).exists() for f in step['produces'])

            # 2. Logic Gate: Check if the task is already "In-Flight"
            in_flight = not self._is_job_stale(step['name'], orchestration_ledger)

            # SCENARIO: Task is ready AND not currently running elsewhere
            if input_evidence and output_missing:
                if in_flight:
                    logger.info(f"⏳ In-Flight Lock Detected: Skipping [{step['name']}] (Active Worker)")
                    continue
                
                logger.info(f"🔍 Forensic Scan: Ready for Dispatch [{step['name']}]")
                ready_steps.append(step)
                continue 

            # SCENARIO: Task already completed
            if input_evidence and not output_missing:
                # If it's in the ledger but finished, it will be cleaned up in main_engine.py
                logger.debug(f"Step [{step['name']}] skipped: Artifacts present.")
                continue

            # SCENARIO: Task blocked (Inputs missing)
            if not input_evidence:
                continue
        
        return ready_steps if ready_steps else None