#!/bin/bash
# ------------------------------------------------------------------------------
# ARCHIVE-DRIVEN SIMULATION ENGINE: SIGNATURE ALIGNMENT
# ------------------------------------------------------------------------------

echo "🔍 INITIATING FINAL SIGNATURE ALIGNMENT..."
echo "========================================================================"

## 1. SMOKING-GUN: Signature/Call Mismatch
echo "❌ AUDIT: Checking test_missing_foundation_halt signature..."
grep -n "def test_missing_foundation_halt" tests/behavior/test_boot_sequence.py

## 2. AUTOMATED REPAIR INJECTIONS (SED)
echo "🛠️  SYNCHRONIZING FIXTURES..."

# If the function body uses fake_foundation, the signature must include it.
# We replace (tmp_path) with (fake_foundation) for consistency across the suite.
sed -i 's/def test_missing_foundation_halt(tmp_path):/def test_missing_foundation_halt(fake_foundation):/g' tests/behavior/test_boot_sequence.py

# Cleanup: Remove the unused empty_dir assignment if it still uses tmp_path
sed -i '/empty_dir = tmp_path/d' tests/behavior/test_boot_sequence.py

## 3. VERIFICATION SCAN
echo "========================================================================"
echo "📊 FINAL ARCHITECTURE PREVIEW:"
cat -n tests/behavior/test_boot_sequence.py | sed -n '106,120p'

# Verify no 'tmp_path' remains in the logic blocks
if grep -q "tmp_path" tests/behavior/test_boot_sequence.py | grep -v "def "; then
    echo "⚠️  Warning: Residual tmp_path detected. Manual review required."
else
    echo "✅ Logic/Fixture Synchronization Complete."
fi
echo "========================================================================"
exit 0