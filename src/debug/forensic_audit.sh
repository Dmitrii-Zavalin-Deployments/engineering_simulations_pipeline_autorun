#!/bin/bash
# ------------------------------------------------------------------------------
# ARCHIVE-DRIVEN SIMULATION ENGINE: SCOPE RECONCILIATION (F821)
# ------------------------------------------------------------------------------

echo "🔍 INITIATING FIXTURE OUTPUT ALIGNMENT..."
echo "========================================================================"

## 1. SMOKING-GUN SOURCE AUDIT
echo "❌ AUDIT: Locating orphaned 'd' variables in test scopes..."
cat -n tests/behavior/test_boot_sequence.py | sed -n '58p;76p;80p;103p;114p'

## 2. AUTOMATED REPAIR INJECTIONS (SED)
echo "🛠️  REPAIRING SCOPE ACCESS..."

# Rule: Tests must access the directory via the fixture's return dictionary.
# We replace 'd' with 'fake_foundation["root"]'.

# Targeted repair for lines identified by Ruff
sed -i 's/\bd \//fake_foundation["root"] \//g' tests/behavior/test_boot_sequence.py
sed -i 's/\bd\//fake_foundation["root"]\//g' tests/behavior/test_boot_sequence.py

# Fix for utime and mount calls specifically
sed -i 's/str(d /str(fake_foundation["root"] /g' tests/behavior/test_boot_sequence.py

## 3. GLOBAL CLEANUP
echo "🧹 Flattening path wrappers..."
sed -i 's/str(str(/str(/g' tests/behavior/test_boot_sequence.py
sed -i 's/)))/))/g' tests/behavior/test_boot_sequence.py

echo "🛠️  Verification pass..."
echo "========================================================================"

## 4. FINAL VERIFICATION
echo "📊 LOGIC PREVIEW (Targeted Lines):"
cat -n tests/behavior/test_boot_sequence.py | sed -n '58p;76p;80p;103p;114p'

# Final Ruff check for F821
if command -v ruff > /dev/null; then
    echo "Running Ruff F821 Audit..."
    ruff check tests/behavior/test_boot_sequence.py --select F821 && echo "✅ NAMESPACE SYNCHRONIZED."
fi

exit 0