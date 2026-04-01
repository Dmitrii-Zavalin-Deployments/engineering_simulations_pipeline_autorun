#!/bin/bash
# src/debug/forensic_audit.sh
# 🔍 Phase C: Undefined Name (F821) Resolution

echo "--- 1. SMOKING GUN: Static Analysis Audit ---"
# Locating exact line numbers where the ghost class is referenced
grep -n "DropboxClient" tests/io/test_download_from_dropbox.py

echo "--- 2. REGISTRY AUDIT: Verified Classes ---"
# Confirming the presence of TokenManager in the source
cat -n src/io/dropbox_utils.py | grep "class "

echo "--- 3. AUTOMATED REPAIRS (Candidate Injections) ---"
# Rule 1 & Rule 2: Synchronize test logic with the Source Registry.

# Repair A: Global replacement of the ghost class with the live implementation
sed -i 's/DropboxClient/TokenManager/g' tests/io/test_download_from_dropbox.py

# Repair B: Verify the replacement (Dry Run)
# grep "TokenManager" tests/io/test_download_from_dropbox.py

echo "--- 4. HYGIENE CHECK (Rule 5) ---"
# Running Ruff again to confirm the 3 remaining errors are purged
ruff check tests/io/test_download_from_dropbox.py || echo "❌ Issues remain"

echo "--- 5. ZERO-DEBT MANDATE (Rule 2) ---"
# Verify that the test file can now be collected by pytest
pytest --collect-only tests/io/test_download_from_dropbox.py