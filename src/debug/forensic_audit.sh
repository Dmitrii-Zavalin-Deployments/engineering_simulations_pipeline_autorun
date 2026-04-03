#!/bin/bash
# 🛰️ NOMADIC ENGINE: DEEP FORENSIC AUDIT (CI FAILURE MODE)
# Targets: Rule 4 (Zero-Default) Violations in Core Logic

echo "=========================================================="
echo "🔍 CI FAILURE DETECTED: INITIATING SMOKING-GUN AUDIT"
echo "=========================================================="

# 1. IDENTIFY RELEVANT VIOLATORS
# Based on CI logs, we focus on: main_engine, state_engine, bootloader, update_ledger
FILES_TO_AUDIT=("src/main_engine.py" "src/core/state_engine.py" "src/core/bootloader.py" "src/core/update_ledger.py")

for FILE in "${FILES_TO_AUDIT[@]}"; do
    if [ -f "$FILE" ]; then
        echo -e "\n--- 📝 AUDITING: $FILE ---"
        # Grep for .get(arg, arg) pattern and display with line numbers and context
        grep -n "\.get(.*,.*)" "$FILE" | while read -r line; do
            LINE_NUM=$(echo "$line" | cut -d: -f1)
            echo "🚩 [RULE 4 VIOLATION] at Line $LINE_NUM:"
            # Display context: 1 line before, the violation, 1 line after
            cat -n "$FILE" | sed -n "$((LINE_NUM-1)),$((LINE_NUM+1))p"
        done
    fi
done

# 2. AUTOMATED REPAIR INJECTIONS
# These seds attempt to convert .get(k, v) into direct access [k] to trigger Hard-Halt
echo -e "\n--- 🛠️ PROPOSED REPAIRS (Rule 4 Hard-Halt Enforcement) ---"

# REPAIR: Replace .get(key, default) with direct access ['key']
# Note: These regexes are aggressive; manual review of the diff is required post-injection.

# # sed -i 's/\.get(\([^,]*\),[^)]*)/[\1]/g' src/main_engine.py
# # sed -i 's/\.get(\([^,]*\),[^)]*)/[\1]/g' src/core/state_engine.py
# # sed -i 's/\.get(\([^,]*\),[^)]*)/[\1]/g' src/core/bootloader.py
# # sed -i 's/\.get(\([^,]*\),[^)]*)/[\1]/g' src/core/update_ledger.py

echo -e "\n--- 🛰️ NOMADIC INTEGRITY CHECK ---"
# Verify if the 'dormant.flag' exists (which might explain why CI is running logic it shouldn't)
if [ -f "config/dormant.flag" ]; then
    echo "⚠️ SYSTEM ALERT: 'dormant.flag' is PRESENT. Engine should be in high-latency mode."
else
    echo "✅ System is in ACTIVE nomadic mode."
fi

echo "=========================================================="
echo "🏁 AUDIT COMPLETE: REPAIR AND RE-COMMIT TO PASS GATE"
echo "=========================================================="