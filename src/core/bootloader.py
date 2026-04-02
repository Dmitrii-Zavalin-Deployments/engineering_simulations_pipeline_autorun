# src/core/bootloader.py

import requests
import logging
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
        """Fetches the remote manifest and hydrates the OrchestrationState."""
        try:
            logger.info(f"🌐 Fetching Remote Manifest: {state.manifest_url}")
            response = requests.get(state.manifest_url, timeout=15)
            response.raise_for_status()
            state.hydrate_manifest(response.json())
            logger.info(f"✅ Boot Sequence Complete: [{state.project_id}] Hydrated.")
        except Exception as e:
            logger.critical(f"Hydration Failed: {e}")
            raise RuntimeError(f"❌ CRITICAL: Hydration failure. {e}")