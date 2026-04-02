#!/bin/bash
# ------------------------------------------------------------------------------
# ARCHIVE-DRIVEN SIMULATION ENGINE: DEEP FORENSIC AUDIT
# Target: CI Failure Analysis (Rule 4, Timezone, and Hydration Errors)
# ------------------------------------------------------------------------------

echo "🔍 INITIATING DEEP FORENSIC AUDIT..."
echo "========================================================================"

## 1. ARCHITECTURAL AUDIT (RULE 4: ZERO-DEFAULT FALLBACK)
echo "❌ AUDIT: Rule 4 Violations (Forbidden .get() usage)"
echo "Checking bootloader.py near line 56..."
sed -n '50,65p' src/core/bootloader.py | cat -n
echo "Checking update_ledger.py near line 75..."
sed -n '70,80p' src/core/update_ledger.py | cat -n

# FIX SUGGESTIONS:
# Replace .get("key", default) with direct access: data["key"]
# sed -i "s/\.get(['\"]timeout_hours['\"], [0-9])/[ 'timeout_hours' ]/g" src/core/update_ledger.py


## 2. TEMPORAL AUDIT (TIMEZONE MISMATCH)
echo "❌ AUDIT: Offset-Naive vs Offset-Aware (state_engine.py:67)"
grep -n "datetime.utcnow()" src/core/state_engine.py
echo "Current state_engine.py comparison logic:"
sed -n '60,75p' src/core/state_engine.py | cat -n

# REPAIR INJECTION:
# Force UTC awareness to match the ISO-formatted ledger strings.
# sed -i "s/datetime.utcnow()/datetime.now(timezone.utc)/g" src/core/state_engine.py


## 3. STRUCTURAL AUDIT (BOOTLOADER & HYDRATION)
echo "❌ AUDIT: Bootloader attribute errors and Missing 'config' in tests"
echo "Does fetch_remote_manifest exist in bootloader.py?"
grep "def fetch_remote_manifest" src/core/bootloader.py || echo "MISSING: Function not found."

echo "Does Bootloader class accept arguments?"
grep -A 2 "class Bootloader" src/core/bootloader.py | cat -n

# REPAIR INJECTION:
# If you moved fetch_remote_manifest to a utility, update tests/behavior/test_boot_sequence.py
# If Bootloader is now a static utility, remove instantiation in tests.


## 4. LEDGER INTEGRITY AUDIT (MISSING TIMEOUT_HOURS)
echo "❌ AUDIT: KeyError 'timeout_hours' in test_scenario_blocked_step"
echo "Inspecting forensic_artifact_scan logic for Rule 4 enforcement:"
sed -n '85,100p' src/core/state_engine.py | cat -n


## 5. REPAIR SUMMARY & SUGGESTED SED INJECTIONS
echo "========================================================================"
echo "📊 REPAIR PROTOCOL:"
echo "1. Fix state_engine.py: Use datetime.now(timezone.utc) for all comparisons."
echo "2. Fix bootloader.py: Remove .get() fallbacks; use direct dict access."
echo "3. Fix tests: Update nomadic_env fixture to include 'config' key to satisfy OrchestrationState init."
echo "========================================================================"

# FINAL EXIT SIGNAL
exit 1