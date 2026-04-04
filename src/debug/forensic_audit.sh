#!/bin/bash
# src/debug/forensic_audit.sh
# 🔍 Forensic Audit: Ledger Namespace Breach

echo "--- 1. SMOKING-GUN SOURCE AUDIT (Namespace Discovery) ---"
# Search for 'class' definitions in state_engine.py to find the actual Ledger handler
grep "class " src/core/state_engine.py

echo -e "\n--- 2. DETAILED SOURCE AUDIT (src/core/state_engine.py) ---"
# Examine the first 100 lines to see if LedgerManager is nested or named differently
cat -n src/core/state_engine.py | head -n 100

echo -e "\n--- 3. USAGE SCAN (main_engine.py) ---"
# Check how the main engine instantiates the ledger to find the correct class
grep -C 2 "ledger" src/main_engine.py

echo -e "\n--- 4. ROOT CAUSE VERIFICATION ---"
if ! grep -q "class LedgerManager" src/core/state_engine.py; then
    echo "CRITICAL: 'LedgerManager' class not found in src/core/state_engine.py."
    echo "Possible cause: The class is named 'Ledger' or the logic is inside 'OrchestrationState'."
fi

echo -e "\n--- 5. AUTOMATED REPAIR INJECTIONS ---"
# If the class is actually named 'Ledger', this repair would align the test:
# sed -i 's/from src.core.state_engine import LedgerManager/from src.core.state_engine import Ledger as LedgerManager/' tests/behavior/test_ledger_traceability.py

# If the logic is actually inside OrchestrationState, we would need to refactor the test.