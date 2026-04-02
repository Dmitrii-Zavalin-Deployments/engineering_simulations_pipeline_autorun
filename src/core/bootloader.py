# src/core/bootloader.py

import requests
import logging
import json
from pathlib import Path
from src.core.state_engine import OrchestrationState

logger = logging.getLogger("Engine.Bootloader")

class Bootloader:
    @staticmethod
    def mount(config_path: str, data_path: str) -> OrchestrationState:
        """
        Mounting Protocol with Auto-Wake Logic.
        Rule: If the config file is newer than the dormancy flag, switch to ACTIVE.
        """
        config_file = Path(config_path)
        dormant_flag = Path("config/dormant.flag")

        if dormant_flag.exists() and config_file.exists():
            # Rule: New config timestamp overrides a stagnant DORMANT status
            if config_file.stat().st_mtime > dormant_flag.stat().st_mtime:
                logger.info("🌅 New Configuration detected. Resetting to STATUS: ACTIVE.")
                try:
                    # Overwrite instead of delete to maintain file structure
                    dormant_flag.write_text("STATUS: ACTIVE", encoding="utf-8")
                except OSError as e:
                    logger.error(f"Failed to reset dormancy flag: {e}")
        
        logger.info(f"🛰️ Mounting Engine Foundation: {config_path}")
        return OrchestrationState(config_path, data_path)

    @staticmethod
    def hydrate(state: OrchestrationState):
        """
        Fetches the remote manifest and enforces Ledger-Project integrity.
        If the Project ID or Manifest ID has changed, the local ledger is reset.
        """
        try:
            logger.info(f"🌐 Fetching Remote Manifest: {state.manifest_url}")
            response = requests.get(state.manifest_url, timeout=15)
            response.raise_for_status()
            remote_manifest = response.json()

            # --- FORENSIC INTEGRITY CHECK ---
            ledger_path = Path("config/orchestration_ledger.json")
            target_pid = remote_manifest.get("project_id")
            target_mid = remote_manifest.get("manifest_id")

            if ledger_path.exists():
                try:
                    ledger_content = json.loads(ledger_path.read_text(encoding="utf-8"))
                    
                    # Extract current identity from ledger metadata
                    meta = ledger_content.get("metadata", {})
                    current_pid = meta.get("project_id")
                    current_mid = meta.get("manifest_id")

                    # Rule: Any ID mismatch triggers a Hard Reset to prevent state pollution
                    if current_pid != target_pid or current_mid != target_mid:
                        logger.warning(f"⚠️ Project/Manifest shift detected: [{current_pid}] -> [{target_pid}].")
                        logger.info("🧹 Performing Forensic Wipe on stale orchestration ledger.")
                        
                        # Initialize clean ledger with new identity
                        fresh_ledger = {
                            "metadata": {
                                "project_id": target_pid,
                                "manifest_id": target_mid
                            },
                            "steps": {}
                        }
                        ledger_path.write_text(json.dumps(fresh_ledger, indent=2), encoding="utf-8")
                        
                except (json.JSONDecodeError, AttributeError) as e:
                    logger.error(f"🚨 Ledger corruption detected: {e}. Wiping for safety.")
                    ledger_path.unlink(missing_ok=True)
            # --- END INTEGRITY CHECK ---

            # Hydrate the state engine with the verified manifest
            state.hydrate_manifest(remote_manifest)
            logger.info(f"✅ Boot Sequence Complete: [{state.project_id}] Hydrated.")
            
        except Exception as e:
            logger.critical(f"Hydration Failed: {e}")
            raise RuntimeError(f"❌ CRITICAL: Hydration failure. {e}")