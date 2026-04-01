# src/core/bootloader.py

import os
import requests
import logging
from pathlib import Path
from src.core.state_engine import OrchestrationState

logger = logging.getLogger("Engine.Bootloader")

class Bootloader:
    """
    TRANSFORMATION LOGIC:
    Transforms a remote URL from active_disk.json into a hydrated OrchestrationState.
    Compliance: Rule 8 (Minimalism) - Static entry points for state transformation.
    """
    
    @staticmethod
    def mount(config_path: str, data_path: str) -> OrchestrationState:
        """
        Mounting Protocol with Auto-Wake Logic.
        Rule: If the config file is newer than the dormancy flag, wake up.
        """
        config_file = Path(config_path)
        dormant_flag = Path("config/dormant.flag")

        if dormant_flag.exists() and config_file.exists():
            if config_file.stat().st_mtime > dormant_flag.stat().st_mtime:
                logger.info("🌅 New Configuration detected. Deleting dormancy flag.")
                try:
                    os.remove(dormant_flag)
                except OSError as e:
                    logger.error(f"Failed to remove dormancy flag: {e}")
        
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