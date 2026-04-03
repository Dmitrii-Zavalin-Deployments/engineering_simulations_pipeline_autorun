#!/bin/bash
# ------------------------------------------------------------------------------
# ARCHIVE-DRIVEN SIMULATION ENGINE: SCOPE & FIXTURE ALIGNMENT
# Target: tests/behavior/test_boot_sequence.py (F821 Undefined Name)
# ------------------------------------------------------------------------------

echo "🔍 INITIATING FIXTURE SCOPE AUDIT..."
echo "========================================================================"

## 1. SMOKING-GUN SOURCE AUDIT
echo "❌ AUDIT: Undefined 'tmp_path' in test_boot_sequence.py"
# Checking lines 58, 77, 81, and 104 where the collision occurred
cat -n tests/behavior/test_boot_sequence.py | sed -n '55,65p;75,85p;100,110p'

## 2. DIAGNOSTIC: VERIFYING FIXTURE SIGNATURES
echo "Checking function signatures for missing fixtures..."
grep -E "def test_.*\(.*\):" tests/behavior/test_boot_sequence.py

## 3. AUTOMATED REPAIR INJECTIONS (SED)
echo "🛠️  GENERATING SCOPE REPAIRS..."

# Strategy: Replace the undefined 'tmp_path' with the 'root' path provided by the 'fake_foundation' fixture.
# This ensures we are pointing to the actual test directory created for that specific run.

# Repair Line 58: Use Path(fake_foundation["root"]) instead of tmp_path
# # sed -i '58s/str(str(tmp_path \/ "missing.json"))/str(Path(fake_foundation["root"]) \/ "missing.json")/' tests/behavior/test_boot_sequence.py

# Repair Lines 77 & 81: Align with the established 'fake_foundation' workspace
# # sed -i '77s/str(tmp_path \/ "missing.json")/str(Path(fake_foundation["root"]) \/ "missing.json")/' tests/behavior/test_boot_sequence.py
# # sed -i '81s/str(str(tmp_path \/ "missing.json"))/str(Path(fake_foundation["root"]) \/ "missing.json")/' tests/behavior/test_boot_sequence.py

# Repair Line 104: Final scope correction for the poisoned manifest test
# # sed -i '104s/str(str(tmp_path \/ "missing.json"))/str(Path(fake_foundation["root"]) \/ "missing.json")/' tests/behavior/test_boot_sequence.py

# Clean up redundant str(str(...)) wrappers introduced by previous edits
# # sed -i 's/str(str(/str(/g' tests/behavior/test_boot_sequence.py
# # sed -i 's/))/)/g' tests/behavior/test_boot_sequence.py

## 4. VERIFICATION SCAN
echo "========================================================================"
echo "📊 POST-REPAIR PREVIEW:"
cat -n tests/behavior/test_boot_sequence.py | sed -n '58p;77p;81p;104p'
echo "========================================================================"

# Pre-flight check for Ruff F821 errors
if command -v ruff > /dev/null; then
    ruff check tests/behavior/test_boot_sequence.py --select F821 && echo "✅ Scope Resolution Successful"
fi

exit 1