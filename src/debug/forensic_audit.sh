#!/bin/bash
# src/debug/forensic_audit.sh
# 🔍 Phase C: High-Fidelity Logic Alignment & Attribute Repair

echo "--- 1. SMOKING GUN: Source Logic Audit ---"
# Verify where call_api actually lives
grep -r "def call_api" src/io/

echo "--- 2. REGISTRY AUDIT: TokenManager vs CloudIngestor ---"
cat -n src/io/dropbox_utils.py | head -n 30
cat -n src/io/download_from_dropbox.py | head -n 30

echo "--- 3. AUTOMATED REPAIRS (Rule 1 Alignment) ---"

# Repair A: Global replacement of the ghost class 'DropboxClient'
# Note: Based on the sh script, we initialize TokenManager first.
# sed -i 's/DropboxClient/TokenManager/g' tests/io/test_download_from_dropbox.py

# Repair B: Correcting the Mock Path for Pagination
# Based on the error, TokenManager has no 'call_api'. It likely belongs to CloudIngestor.
# sed -i "s/patch('src.io.dropbox_utils.TokenManager.call_api')/patch('src.io.download_from_dropbox.CloudIngestor.call_api')/g" tests/io/test_download_from_dropbox.py

# Repair C: Dependency Injection Alignment (Rule 4)
# TokenManager requires (client_id, client_secret)
# sed -i 's/TokenManager()/TokenManager("mock_id", "mock_secret")/g' tests/io/test_download_from_dropbox.py

echo "--- 4. DETERMINISTIC VERIFICATION ---"
# Rule 5: Hygiene Check
ruff check tests/io/test_download_from_dropbox.py --fix

echo "--- 5. FINAL SIGNAL (Rule 2) ---"
# Execute the specific failed test file
pytest tests/io/test_download_from_dropbox.py