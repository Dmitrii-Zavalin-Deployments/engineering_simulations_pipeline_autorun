#!/bin/bash
# src/debug/forensic_audit.sh
# 🔍 Phase D: Tier-Gap Alignment & Logic Synchronization

echo "--- 1. SMOKING GUN: Data Structure Audit ---"
# Check if forensic_artifact_scan returns a list or a single object
grep -A 5 "def forensic_artifact_scan" src/core/state_engine.py

echo "--- 2. REGISTRY AUDIT: Dispatcher Environment ---"
# Verify the exact variable name used in the constructor
grep "os.getenv" src/api/github_trigger.py

echo "--- 3. AUTOMATED REPAIRS (Rule 1, 4 & 5) ---"

# Repair A: Fix TypeError (Data Structure Alignment)
# If the scan returns a list, the tests must access index [0]
# sed -i "s/gap = state.forensic_artifact_scan()/gap = state.forensic_artifact_scan()[0]/g" tests/test_integration_gate.py
# sed -i "s/target = state_manager.forensic_artifact_scan()/target = state_manager.forensic_artifact_scan()[0]/g" tests/core/test_forensic_logic.py
# sed -i "s/step = future_engine_setup.forensic_artifact_scan()/step = future_engine_setup.forensic_artifact_scan()[0]/g" tests/core/test_future_proof.py

# Repair B: Fix RuntimeError (Token Registry Alignment)
# Update tests to use GH_PAT to match the source code logic
# sed -i "s/GITHUB_TOKEN/GH_PAT/g" tests/api/test_dispatch_logic.py
# sed -i "s/GITHUB_TOKEN/GH_PAT/g" tests/test_integration_gate.py

# Repair C: Fix AssertionError (Regex Match Alignment)
# sed -i "s/GITHUB_TOKEN not found/GH_PAT not found/g" tests/api/test_dispatch_logic.py

# Repair D: Fix FileExistsError (Bootloader Path Logic)
# Ensure OrchestrationState doesn't try to mkdir on the schema file path
# sed -i "s/self.data_path.mkdir/if not self.data_path.is_file(): self.data_path.mkdir/g" src/core/state_engine.py

# Repair E: Fix Ingestor Mock Leak
# We must patch requests.post BEFORE initializing CloudIngestor in the pagination test
# sed -i '/tm = TokenManager/i \ \ \ \ \ \ \ \ with patch("requests.post") as m: m.return_value.status_code=200; m.return_value.json.return_value={"access_token":"mock"}' tests/io/test_download_from_dropbox.py

echo "--- 4. DETERMINISTIC VERIFICATION ---"
# pytest tests/