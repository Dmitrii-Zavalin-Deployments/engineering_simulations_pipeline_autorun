#!/bin/bash
# src/debug/forensic_audit.sh
# 🔍 Diagnosis of Gate Priority Conflict (Phase A vs Phase B)

echo "--- 1. SMOKING GUN: GATE SEQUENCE AUDIT ---"
# Locating the current order of checks in hydrate_manifest
cat -n src/core/state_engine.py | sed -n '48,65p'

echo "--- 2. LOGIC LEAK DETECTION ---"
# Verify if the Schema Validation block is reachable after the Identity Guard
grep -n "validate(" src/core/state_engine.py

echo "--- 3. AUTOMATED REPAIR (SED INJECTIONS) ---"
# To fix the test, we must wrap the Identity Mismatch in the "CRITICAL: Hard-Halt" 
# prefix or move it after Schema Validation.

# REPAIR: Prepend the required test signature to the RuntimeError message
# sed -i 's/raise RuntimeError(f"Identity Mismatch/raise RuntimeError(f"CRITICAL: Hard-Halt - Identity Mismatch/' src/core/state_engine.py

# ALTERNATIVE REPAIR: Re-ordering gates so Schema check happens first
# Step A: Delete the current Identity Guard lines (51-52)
# sed -i '51,52d' src/core/state_engine.py
# Step B: Inject Identity Guard AFTER the try/except validation block (around line 58)
# sed -i '/validate(instance=manifest_json, schema=schema)/a \            if manifest_json.get("project_id") != self.project_id:\n                raise RuntimeError(f"CRITICAL: Hard-Halt - Identity Mismatch: {manifest_json.get(\"project_id\")} != {self.project_id}")' src/core/state_engine.py

echo "--- 4. POST-REPAIR VERIFICATION ---"
python3 -m py_compile src/core/state_engine.py && echo "✅ Syntax Valid." || echo "❌ Syntax Error."

echo "Audit Complete. Run the # sed commands to align with the Constitution's error signatures."