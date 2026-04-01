#!/bin/bash
# src/debug/forensic_audit.sh
# 🛠️ Phase C: Logic Alignment & F821 Undefined Name Repair

echo "--- 1. SMOKING GUN: Source Analysis ---"
# Verify the current state of the test file
cat -n tests/io/test_download_from_dropbox.py | sed -n '30,75p'

echo "--- 2. AUTOMATED REPAIRS (Rule 1 Alignment) ---"

# Repair A: Replace all remaining references of the ghost class in logic and mocks
sed -i 's/DropboxClient/TokenManager/g' tests/io/test_download_from_dropbox.py

# Repair B: Ensure the mock patch path is also updated to the live implementation
# (This fixes line 47 where it tries to patch a non-existent class path)
sed -i "s/patch('src.io.dropbox_utils.DropboxClient/patch('src.io.dropbox_utils.TokenManager/g" tests/io/test_download_from_dropbox.py

echo "--- 3. HYGIENE CHECK (Rule 5) ---"
# Confirm Ruff is now satisfied with the local namespace
ruff check tests/io/test_download_from_dropbox.py --fix

echo "--- 4. FINAL SIGNAL (Rule 2) ---"
# Attempt to run the collected 3 tests to verify the repair
pytest tests/io/test_download_from_dropbox.py