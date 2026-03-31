# src/core/state_engine.py

import json
import os
from pathlib import Path

class OrchestrationState:
    """
    The 'Console' State. 
    Hydrated from the Manifest, it performs the Forensic Artifact Scan 
    to determine the current reality of the simulation.
    """
    __slots__ = ['project_id', 'manifest_url', 'data_path', 'manifest_data']

    def __init__(self, config_path: str, data_root: str):
        self.data_path = Path(data_root)
        
        # Ensure the foundation exists
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Mounting Protocol: Identify the mission
        with open(config_path, 'r') as f:
            config = json.load(f)
            self.project_id = config['project_id']
            self.manifest_url = config['manifest_url']
        
        self.manifest_data = None

    def hydrate_manifest(self, manifest_json: dict):
        """Injects the external manifest logic into the ephemeral state."""
        self.manifest_data = manifest_json

    def forensic_artifact_scan(self):
        """
        Deterministic Idempotency Rule: 
        Interrogates the filesystem. A step triggers ONLY if:
        - Requirements (Inputs) EXIST
        - Productions (Outputs) are MISSING
        """
        if not self.manifest_data:
            raise RuntimeError("Engine not hydrated. Insert Manifest before scanning.")

        for step in self.manifest_data.get("pipeline_steps", []):
            name = step['name']
            requires = step.get("requires", [])
            produces = step.get("produces", [])

            # Evidence-Based Check
            input_evidence = all((self.data_path / f).exists() for f in requires)
            output_missing = any(not (self.data_path / f).exists() for f in produces)

            if input_evidence and output_missing:
                print(f"🔍 Forensic Scan: Gap detected at step [{name}]")
                return step
        
        print("🔍 Forensic Scan: All artifacts accounted for. Pipeline saturated.")
        return None