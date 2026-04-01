#!/bin/bash
# src/debug/forensic_audit.sh
# 🛠️ Phase C: Namespace & Dependency Injection Repair

echo "--- 1. SMOKING GUN: Import Audit ---"
head -n 15 tests/io/test_download_from_dropbox.py

echo "--- 2. AUTOMATED REPAIRS (Rule 1 & Rule 4 Alignment) ---"

# Repair A: Ensure the correct class is imported from the utility registry
sed -i 's/from src.io.dropbox_utils import.*/from src.io.dropbox_utils import TokenManager/g' tests/io/test_download_from_dropbox.py

# Repair B: Fix the initialization to include required mock credentials (Rule 4)
# TokenManager requires (client_id, client_secret) as per src/io/dropbox_utils.py line 28
sed -i 's/TokenManager()/TokenManager("mock_id", "mock_secret")/g' tests/io/test_download_from_dropbox.py

# Repair C: Fix the patch path for the API call mock (Line 47)
sed -i "s/patch('src.io.dropbox_utils.DropboxClient/patch('src.io.dropbox_utils.TokenManager/g" tests/io/test_download_from_dropbox.py

echo "--- 3. HYGIENE CHECK (Rule 5) ---"
# Verify that F821 errors are cleared
ruff check tests/io/test_download_from_dropbox.py

echo "--- 4. FINAL SIGNAL (Rule 2) ---"
# Run the tests to confirm the 'Truth vs Logic' calculation is restored
pytest tests/io/test_download_from_dropbox.py