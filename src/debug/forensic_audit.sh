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

# Repair A: Fix Import Registry
sed -i 's/from src.io.dropbox_utils import DropboxClient/from src.io.dropbox_utils import TokenManager/g' tests/io/test_download_from_dropbox.py
# Ensure CloudIngestor is also available if needed for call_api mocks
sed -i '/import TokenManager/a from src.io.download_from_dropbox import CloudIngestor' tests/io/test_download_from_dropbox.py

# Repair B: Global replacement of the ghost class and Dependency Injection (Rule 4)
sed -i 's/DropboxClient()/TokenManager("mock_id", "mock_secret")/g' tests/io/test_download_from_dropbox.py

# Repair C: Correcting the Mock Path for Pagination
# Point mock to the functional class (CloudIngestor) instead of the credential class (TokenManager)
sed -i "s/patch('src.io.dropbox_utils.TokenManager.call_api')/patch('src.io.download_from_dropbox.CloudIngestor.call_api')/g" tests/io/test_download_from_dropbox.py

echo "--- 4. DETERMINISTIC VERIFICATION ---"
# Rule 5: Hygiene Check
ruff check tests/io/test_download_from_dropbox.py --fix

echo "--- 5. FINAL SIGNAL (Rule 2) ---"
pytest tests/io/test_download_from_dropbox.py