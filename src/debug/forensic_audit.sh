#!/bin/bash
# ------------------------------------------------------------------------------
# ARCHIVE-DRIVEN SIMULATION ENGINE: FINAL SCOPE ALIGNMENT
# ------------------------------------------------------------------------------

echo "🔍 INITIATING AGGRESSIVE SCOPE REPAIR..."
echo "========================================================================"

## 1. SMOKING-GUN SOURCE AUDIT
echo "❌ AUDIT: Finding remaining 'tmp_path' in test_boot_sequence.py..."
grep -n "tmp_path" tests/behavior/test_boot_sequence.py

## 2. AUTOMATED REPAIR INJECTIONS (SED)
echo "🛠️  PERFORMING SURGICAL REPLACEMENTS..."

# This regex finds any instance of str(...) containing tmp_path and "missing.json" 
# and converts it into a single clean Path call using the fake_foundation fixture.
sed -i 's/str(str(tmp_path \/ "missing.json"))/str(Path(fake_foundation["root"]) \/ "missing.json")/g' tests/behavior/test_boot_sequence.py
sed -i 's/str(tmp_path \/ "missing.json")/str(Path(fake_foundation["root"]) \/ "missing.json")/g' tests/behavior/test_boot_sequence.py

# Fix for line 16 and 111 (Generic tmp_path usage in setup)
sed -i 's/d = tmp_path \/ "project_root"/d = Path(fake_foundation["root"]) \/ "project_root"/g' tests/behavior/test_boot_sequence.py
sed -i 's/empty_dir = tmp_path \/ "empty_vault"/empty_dir = Path(fake_foundation["root"]) \/ "empty_vault"/g' tests/behavior/test_boot_sequence.py

# Fix for line 117 (Halt test)
sed -i '117s/str(str(tmp_path \/ "missing.json"))/str(Path(fake_foundation["root"]) \/ "missing.json")/' tests/behavior/test_boot_sequence.py

## 3. GLOBAL CLEANUP
echo "🧹 Cleaning up nested str() calls..."
sed -i 's/str(str(/str(/g' tests/behavior/test_boot_sequence.py
sed -i 's/json"))/json")/g' tests/behavior/test_boot_sequence.py

## 4. VERIFICATION SCAN
echo "========================================================================"
echo "📊 POST-REPAIR PREVIEW (Targets 58, 77, 81, 104, 117):"
cat -n tests/behavior/test_boot_sequence.py | sed -n '58p;77p;81p;104p;117p'

# Check if we need to add 'from pathlib import Path'
if ! grep -q "from pathlib import Path" tests/behavior/test_boot_sequence.py; then
    echo "⚠️ Path import missing. Injecting..."
    sed -i '1i from pathlib import Path' tests/behavior/test_boot_sequence.py
fi

if command -v ruff > /dev/null; then
    ruff check tests/behavior/test_boot_sequence.py --select F821 && echo "✅ F821 Scope Errors Resolved"
fi
echo "========================================================================"
exit 1