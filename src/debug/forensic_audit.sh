#!/bin/bash
# src/debug/forensic_audit.sh
# 🔍 Phase C: Forensic Alignment & Dead-Link Repair

echo "--- 1. SMOKING GUN: Source Audit (src/io/dropbox_utils.py) ---"
# Rule 1: Verify the actual class names in the Forensic Registry
cat -n src/io/dropbox_utils.py | grep -E "class |def "

echo "--- 2. WIRING AUDIT: Test Import Integrity ---"
# Identifying the broken link in the test suite
grep -n "from src.io.dropbox_utils import" tests/io/test_download_from_dropbox.py

echo "--- 3. DETERMINISTIC REPAIR (Candidate Injections) ---"
# Rule 0 & Rule 2: Fix the import mismatch to restore the Quality Gate.
# If 'TokenManager' is the intended class, use the following repair:

# Repair: Align test import with TokenManager
# sed -i 's/DropboxClient/TokenManager/g' tests/io/test_download_from_dropbox.py

# Repair: Align test import with CloudIngestor (if that was the target)
# sed -i 's/DropboxClient/CloudIngestor/g' tests/io/test_download_from_dropbox.py

echo "--- 4. DEPENDENCY VALIDATION ---"
# Verify jsonschema is now properly hydrated in the environment
pip list | grep jsonschema || echo "⚠️ Warning: jsonschema still missing from environment"

echo "--- 5. COVERAGE PRE-FLIGHT ---"
# Calculate logic-to-test ratio to identify gaps in the Zero-Debt Mandate
python3 -c "import os; print(f'Logic files: {len(os.listdir(\"src/core\"))} | Test files: {len(os.listdir(\"tests/core\"))}')"