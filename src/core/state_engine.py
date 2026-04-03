# src/core/state_engine.py

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from jsonschema import validate

# Internal Core Imports
from src.core.constants import OrchestrationStatus, SystemPaths

logger = logging.getLogger("Engine.State")

class OrchestrationState:
    """
    Forensic Artifact Registry.
    Implements the 'Round-and-Round' Transition Matrix for Nomadic Automation.
    Phase C Compliance: Rule 0 (__slots__), Idempotency Contract, and Schema Sovereignty.
    """
    __slots__ = ['project_id', 'manifest_url', 'data_path', 'manifest_data', 'schema_path']

    def __init__(self, config_path: str, data_root: str):
        self.data_path = Path(data_root)
        # Standardized via SystemPaths
        self.schema_path = Path(SystemPaths.CONFIG_DIR) / "core_schema.json"
        
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
        """Enforces Schema Sovereignty before allowing hydration."""
        try:
            with open(self.schema_path, 'r', encoding="utf-8") as s:
                schema = json.load(s)
            validate(instance=manifest_json, schema=schema)
            self.manifest_data = manifest_json
            logger.info(f"💿 Registry Hydrated & Validated: [{manifest_json['manifest_id']}]")
        except Exception as e:
            raise RuntimeError(f"❌ CRITICAL: Hard-Halt. Manifest is corrupt. {e}")

    def _is_job_stale(self, job_name: str, ledger: dict) -> bool:
        """Helper: Checks if a job's time-lock has expired."""
        job_data = ledger[job_name]
        try:
            timeout_h = job_data["timeout_hours"]
            last_trigger_str = job_data["last_triggered"]
            last_trigger = datetime.fromisoformat(last_trigger_str)
            return datetime.now(timezone.utc) > (last_trigger + timedelta(hours=timeout_h))
        except (KeyError, ValueError, TypeError):
            # If timing data is corrupted or missing, assume stale to allow recovery
            return True

    def reconcile_and_heal(self, orchestration_ledger: dict):
        """
        The Core Logic Loop: Reconciles the Ledger against Physical Reality.
        Implements the 30-minute 'Round-and-Round' Transition Matrix.
        """
        if not self.manifest_data:
            raise RuntimeError("❌ CRITICAL: Scan attempted without Manifest Hydration.")

        for step in self.manifest_data["pipeline_steps"]:
            name = step["name"]
            
            # Ensure the step exists in the ledger metadata
            if name not in orchestration_ledger:
                orchestration_ledger[name] = {"status": OrchestrationStatus.WAITING.value}
            
            entry = orchestration_ledger[name]
            current_status = entry["status"]
            
            # PHYSICAL TRUTH CHECK
            requires = step["requires"]
            produces = step["produces"]
            inputs_exist = all((self.data_path / f).exists() for f in requires)
            outputs_exist = all((self.data_path / f).exists() for f in produces)

            # --- TRANSITION LOGIC (As per engine_protocol_v3.html) ---

            # 1. UNIVERSAL TRUTH: If artifacts exist, it's COMPLETED regardless of previous status
            if outputs_exist:
                if current_status != OrchestrationStatus.COMPLETED.value:
                    logger.info(f"✅ {name}: Success verified. Status flipped to COMPLETED.")
                entry["status"] = OrchestrationStatus.COMPLETED.value

            # 2. WAITING -> PENDING
            elif current_status == OrchestrationStatus.WAITING.value and inputs_exist:
                logger.info(f"🔓 {name}: Inputs detected. Status flipped to PENDING.")
                entry["status"] = OrchestrationStatus.PENDING.value

            # 3. PENDING -> WAITING (Safety Reversion)
            elif current_status == OrchestrationStatus.PENDING.value and not inputs_exist:
                logger.warning(f"⚠️ {name}: Input artifacts missing. Reverting to WAITING.")
                entry["status"] = OrchestrationStatus.WAITING.value

            # 4. IN_PROGRESS GATES
            elif current_status == OrchestrationStatus.IN_PROGRESS.value:
                if self._is_job_stale(name, orchestration_ledger):
                    logger.error(f"⌛ {name}: Execution Timeout. Status flipped to FAILED.")
                    entry["status"] = OrchestrationStatus.FAILED.value
                else:
                    logger.info(f"⏳ {name}: Still in progress (within timeout window).")

            # 5. COMPLETED DRIFT (The "Liar Ledger" Case)
            elif current_status == OrchestrationStatus.COMPLETED.value and not outputs_exist:
                logger.warning(f"🚨 {name}: Artifact drift detected (File Missing). Reverting to WAITING.")
                entry["status"] = OrchestrationStatus.WAITING.value

            # 6. FAILED RECOVERY
            elif current_status == OrchestrationStatus.FAILED.value:
                if inputs_exist:
                    logger.info(f"🔄 {name}: Retrying... Status flipped to PENDING.")
                    entry["status"] = OrchestrationStatus.PENDING.value
                else:
                    logger.info(f"🛑 {name}: Retry blocked by data gap. Status flipped to WAITING.")
                    entry["status"] = OrchestrationStatus.WAITING.value

        return orchestration_ledger

    def get_ready_steps(self, orchestration_ledger: dict):
        """Returns steps currently in PENDING status for the main_engine to trigger."""
        ready_steps = []
        for step in self.manifest_data["pipeline_steps"]:
            name = step["name"]
            status = orchestration_ledger[name]["status"]
            if status == OrchestrationStatus.PENDING.value:
                ready_steps.append(step)
        return ready_steps if ready_steps else None