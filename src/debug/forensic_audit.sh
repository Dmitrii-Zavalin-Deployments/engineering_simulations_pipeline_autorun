#!/bin/bash
# 🕵️ Forensic Audit: Engine Logic Breach & Environment gaps

echo "--- 1. SMOKING GUN: Missing Schema in Test Environment ---"
# Locating why Bootloader fails to find the validation schema
find /tmp -name "active_disk_schema.json" || echo "❌ Result: active_disk_schema.json is missing from temp nodes."

echo "--- 2. SOURCE AUDIT: state_engine.py (Line 122) ---"
# Examining the hydration gate that caused the RuntimeError
cat -n src/core/state_engine.py | sed -n '115,130p'

echo "--- 3. SOURCE AUDIT: main_engine.py (Hydration Point) ---"
# Verifying how orchestration_data is passed to reconcile_and_heal
cat -n src/main_engine.py | sed -n '40,60p'

echo "--- 4. AUTOMATED REPAIR: Mock Hydration Injection ---"
# To fix the tests, we need to ensure the StateEngineDummy.create() 
# also produces the required schema files for the Bootloader.

# Repair 1: Inject schema creation into StateEngineDummy (conceptual)
# sed -i '/schema_dir.mkdir/a \            (schema_dir / "active_disk_schema.json").write_text("{\"type\":\"object\"}")' tests/helpers/state_engine_dummy.py

# Repair 2: Fix test_main_engine.py to manually hydrate the state object 
# when mocking Bootloader.hydrate to prevent the RuntimeError.
# sed -i '/mock_hydrate.return_value = /a \        state.hydrate_manifest({"manifest_id": "TEST", "project_id": "TEST", "pipeline_steps": []})' tests/test_main_engine.py

echo "--- 5. COVERAGE GAP ANALYSIS ---"
# Checking why main_engine.py is stuck at 48%
grep -A 5 "src/main_engine.py" coverage.txt || echo "Run pytest --cov first."