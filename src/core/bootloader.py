# src/core/bootloader.py

import json
import requests
import logging
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
        """Initializes the state object using local configuration."""
        logger.info(f"🛰️ Mounting Engine Foundation from: {config_path}")
        return OrchestrationState(config_path, data_path)

    @staticmethod
    def hydrate(state: OrchestrationState):
        """
        Remote Manifest Ingestion:
        Fetches the raw JSON from state.manifest_url and hydrates the registry.
        """
        try:
            logger.info(f"🌐 Fetching Remote Manifest: {state.manifest_url}")
            response = requests.get(state.manifest_url, timeout=15)
            response.raise_for_status()
            
            manifest_data = response.json()
            
            # The 'Hydration Gate' - Structural validation happens inside state_engine
            state.hydrate_manifest(manifest_data)
            logger.info(f"✅ Boot Sequence Complete: [{state.project_id}] Hydrated.")
            
        except requests.exceptions.RequestException as e:
            logger.critical(f"Hydration Failed: Connection Error. {e}")
            raise RuntimeError(f"❌ CRITICAL: Could not reach manifest URL. {e}")
        except json.JSONDecodeError:
            logger.critical("Hydration Failed: Remote manifest is not valid JSON.")
            raise RuntimeError("❌ CRITICAL: Remote manifest corrupted.")