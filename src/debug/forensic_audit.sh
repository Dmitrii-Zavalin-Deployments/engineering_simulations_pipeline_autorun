#!/bin/bash
# src/debug/forensic_audit.sh
# 🔍 Phase C: High-Fidelity Namespace & Attribute Repair

echo "--- 1. SMOKING GUN: Class & Method Audit ---"
# Verify the actual methods available in CloudIngestor to fix the AttributeError
grep "def " src/io/download_from_dropbox.py

echo "--- 2. REGISTRY AUDIT: Import Integrity ---"
# Check the top of the test file for missing imports
head -n 20 tests/io/test_download_from_dropbox.py

echo "--- 3. AUTOMATED REPAIRS (Rule 1 & 5 Alignment) ---"

# Repair A: Inject missing imports into the test file
sed -i '/import os/a from src.io.dropbox_utils import TokenManager' tests/io/test_download_from_dropbox.py
sed -i '/import TokenManager/a from src.io.download_from_dropbox import CloudIngestor' tests/io/test_download_from_dropbox.py

# Repair B: Fix the AttributeError by patching the correct Dropbox SDK call
# Instead of a non-existent 'call_api', we patch the underlying SDK method used by the ingestor
sed -i "s/patch('src.io.download_from_dropbox.CloudIngestor.call_api')/patch('dropbox.Dropbox.files_list_folder')/g" tests/io/test_download_from_dropbox.py

# Repair C: Final Name Alignment
# Ensure no ghost references to DropboxClient remain in the logic
sed -i 's/DropboxClient/TokenManager/g' tests/io/test_download_from_dropbox.py

echo "--- 4. DETERMINISTIC VERIFICATION ---"
# Rule 5: Hygiene Check
ruff check tests/io/test_download_from_dropbox.py --fix || echo "⚠️ Ruff found deep logic issues"

echo "--- 5. FINAL SIGNAL (Rule 2) ---"
# Re-run the tests to verify the Sovereign Logic Gate is restored
pytest tests/io/test_download_from_dropbox.py