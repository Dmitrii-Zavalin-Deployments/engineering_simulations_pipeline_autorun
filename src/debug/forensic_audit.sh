#!/bin/bash
# 🛠️ Automated Repair: Restoring Physical & Memory Integrity

echo "--- 1. REPAIR: Injecting Missing Schemas into Test Setup ---"
# This ensures the Bootloader satisfies Rule 4 (Zero-Default) during the mount phase.
sed -i '/state, data_dir = mock_env/a \    schema_dir = data_dir.parent / "schema"\n    schema_dir.mkdir(parents=True, exist_ok=True)\n    (schema_dir / "active_disk_schema.json").write_text("{\\"type\\":\\"object\\"}")\n    (schema_dir / "manifest_schema.json").write_text("{\\"type\\":\\"object\\"}")' tests/test_main_engine.py

echo "--- 2. REPAIR: Forcing Manual Hydration in Mocked Tests ---"
# Since we bypass Bootloader.hydrate(), we must manually seed the state object 
# to prevent the RuntimeError at state_engine.py:122.
sed -i '/mock_hydrate.return_value = /a \        state.hydrate_manifest({"manifest_id": "TEST-MID", "project_id": "TEST-PID", "pipeline_steps": []})' tests/test_main_engine.py

echo "--- 3. SOURCE VERIFICATION: main_engine.py Line 54 ---"
# Ensuring the engine passes the correct 'steps' key from the hydration result.
cat -n src/main_engine.py | sed -n '50,60p'

echo "--- 4. COVERAGE RECOVERY ---"
# Triggering a fresh coverage report to analyze the 48% bottleneck.
pytest --cov=src tests/test_main_engine.py > coverage_report.txt
grep "src/main_engine.py" coverage_report.txt