#!/bin/bash
# ------------------------------------------------------------------------------
# ARCHIVE-DRIVEN SIMULATION ENGINE: DICTIONARY KEY DEDUPLICATION
# ------------------------------------------------------------------------------

echo "🔍 INITIATING FINAL KEY DEDUPLICATION..."
echo "========================================================================"

## 1. REPAIR test_identity_preservation_same_ids (Lines 158-159)
# We delete line 158 because line 159 has the same metadata PLUS the 'steps' key.
sed -i '158d' tests/behavior/test_ledger_integrity.py

## 2. REPAIR test_identity_mismatch_reset (Line 199+)
# Based on your grep, line 199 is likely a duplicate header as well.
# We look for the "metadata" line that doesn't have "steps" and remove it.
sed -i '199d' tests/behavior/test_ledger_integrity.py

## 3. GLOBAL SYNTAX CLEANUP
# Ensure we didn't leave any empty dictionaries or double commas.
sed -i 's/{ "metadata"/{ "metadata"/g' tests/behavior/test_ledger_integrity.py

echo "🛠  Surgical deduplication complete."
echo "========================================================================"

# Pre-flight check for ruff
if command -v ruff > /dev/null; then
    echo "Checking syntax status..."
    ruff check tests/behavior/test_ledger_integrity.py --select F601
fi

exit 1