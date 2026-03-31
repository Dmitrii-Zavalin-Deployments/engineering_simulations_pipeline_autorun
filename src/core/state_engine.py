# src/core/state_engine.py

import json
from pathlib import Path

class OrchestrationState:
    """
    The 'Console' State. 
    Hydrated from the Manifest, it performs the Forensic Artifact Scan 
    to determine the current reality of the simulation.
    
    Phase C Compliance: Rule 0 (__slots__) and Rule 4 (Zero-Default Policy).
    """
    __slots__ = ['project_id', 'manifest_url', 'data_path', 'manifest_data']

    def __init__(self, config_path: str, data_root: str):
        self.data_path = Path(data_root)
        
        # Ensure the foundation exists (The Infrastructure Sink)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Mounting Protocol: Phase A, Section 1 (Single-Slot Rule)
        with open(config_path, 'r') as f:
            config = json.load(f)
            # Rule 4: Explicit assignment ensures early failure if config is malformed
            self.project_id = config['project_id']
            self.manifest_url = config['manifest_url']
        
        self.manifest_data = None

    def hydrate_manifest(self, manifest_json: dict):
        """Injects the external manifest logic into the ephemeral state."""
        self.manifest_data = manifest_json

    def forensic_artifact_scan(self):
        """
        Deterministic Idempotency Rule: 
        Interrogates the physical /data directory.
        Rule 4 Compliance: No .get() fallbacks. Explicit or Error.
        """
        if not self.manifest_data:
            raise RuntimeError("Engine not hydrated. Insert Manifest before scanning.")

        # Phase C, Rule 4: Access keys directly. 
        # If 'pipeline_steps' is missing, the engine MUST crash to prevent silent debt.
        for step in self.manifest_data["pipeline_steps"]:
            name = step['name']
            requires = step['requires']
            produces = step['produces']

            # Evidence-Based Check: Truth exists only in physical artifacts
            input_evidence = all((self.data_path / f).exists() for f in requires)
            output_missing = any(not (self.data_path / f).exists() for f in produces)

            if input_evidence and output_missing:
                print(f"🔍 Forensic Scan: Gap detected at step [{name}]")
                return step
        
        print("🔍 Forensic Scan: All artifacts accounted for. Pipeline saturated.")
        return None