#!/bin/bash
# src/debug/forensic_audit.sh
# 🔍 Phase G: Final Indentation Realignment & Header Sync

echo "--- 1. SMOKING GUN: Indentation Audit ---"
cat -n tests/api/test_dispatch_logic.py | sed -n '57,63p'

echo "--- 2. AUTOMATED REPAIRS ---"

# Repair A: Fix Indentation on the Skip Guard (Line 60-61)
# We remove the excessive leading whitespace and align it with 'success'
# sed -i '60s/^[[:space:]]*/    /' tests/api/test_dispatch_logic.py
# sed -i '61s/^[[:space:]]*/        /' tests/api/test_dispatch_logic.py

# Repair B: Global Header Audit
# Ensure necessary modules are imported to prevent NameError
# grep -q "import os" tests/api/test_dispatch_logic.py || sed -i '1i import os' tests/api/test_dispatch_logic.py
# grep -q "import pytest" tests/api/test_dispatch_logic.py || sed -i '1i import pytest' tests/api/test_dispatch_logic.py

# Repair C: Clean Room Format
# Use ruff to fix any remaining spacing inconsistencies now that syntax is valid
# ruff format tests/api/test_dispatch_logic.py

echo "--- 3. DETERMINISTIC VERIFICATION ---"
# Verify syntax validity before running pytest
python3 -m py_compile tests/api/test_dispatch_logic.py && echo "✅ Syntax Validated."

echo "📉 RE-RUNNING FAILED TEST FOR FINAL SIGNAL"
pytest tests/