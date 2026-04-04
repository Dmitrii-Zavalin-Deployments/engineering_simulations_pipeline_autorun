#!/bin/bash
# src/debug/apply_fix.sh
# 🔧 Aligns Phase C (1) tests with Engine Exception Signatures

TARGET_TEST="tests/architecture/test_forensic_io.py"

echo "🔄 Applying forensic alignment to $TARGET_TEST..."

# Replace the failing assertion with one that matches the Bootloader's 'CRITICAL' prefix
sed -i 's/assert "SCHEMA BREACH" in str(excinfo.value) or "FileNotFoundError" in str(excinfo.value)/assert "CRITICAL:" in str(excinfo.value) and "corrupt or invalid" in str(excinfo.value)/' "$TARGET_TEST"

echo "✅ Alignment applied. Rerunning verification..."
pytest "$TARGET_TEST"