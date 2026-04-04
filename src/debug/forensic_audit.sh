#!/bin/bash
# Description: Automated forensic audit for Navier-Stokes solver failures.
# Status: Dormant (All systems nominal)
exit 0
#!/bin/bash
# src/debug/forensic_audit.sh
# 🔍 Forensic Audit: Phase A Isolation Breach & Mounting Failure

echo "--- 1. SMOKING-GUN SOURCE AUDIT (src/core/state_engine.py) ---"
# Check the exact lines where the Hard-Halt is triggered
cat -n src/core/state_engine.py | sed -n '35,48p'

echo -e "\n--- 2. TEST FAILURE DIAGNOSTICS (tests/behavior/test_artifact_forensics.py) ---"
# Audit the test to see the missing file-write operation
cat -n tests/behavior/test_artifact_forensics.py | sed -n '60,70p'

echo -e "\n--- 3. ROOT CAUSE VERIFICATION ---"
if grep -q "str(tmp_path/\"disk.json\")" tests/behavior/test_artifact_forensics.py; then
    echo "Found: Test attempts to initialize StateEngine with a non-existent disk.json."
    echo "Logic Breach: Protocol requires physical 'Mounting' before initialization."
fi

echo -e "\n--- 4. AUTOMATED REPAIR INJECTIONS ---"
# These sed commands will fix the test by seeding the required config file before init
# Use these to repair the test_clean_room_isolation function:

# Step A: Inject the missing json import if not present
# sed -i '1i import json' tests/behavior/test_artifact_forensics.py

# Step B: Inject the 'disk.json' seeding logic before the OrchestrationState call
# sed -i '/state = OrchestrationState(str(tmp_path\/\"disk.json\")/i \    (tmp_path / "disk.json").write_text(json.dumps({"project_id": "ISO-TEST", "manifest_url": "http://mock.com"}))' tests/behavior/test_artifact_forensics.py

echo "--- 5. REPAIR VERIFICATION ---"
echo "To fix manually, update test_clean_room_isolation to write the config file:"
echo "    config = tmp_path / 'disk.json'"
echo "    config.write_text(json.dumps({'project_id': 'TEST', 'manifest_url': 'URL'}))"
echo "    state = OrchestrationState(str(config), ...)"