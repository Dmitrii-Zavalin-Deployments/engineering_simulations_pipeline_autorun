#!/bin/bash
# 🕵️ Forensic Audit: Schema Asset Displacement & API Drift
# Run this post-test in GitHub Actions to catch the smoking gun.

echo "--- 📂 [1/4] INSTANCE TOPOGRAPHY ---"
echo "Current Working Directory: $(pwd)"
echo "Checking for 'schema' at Execution Root:"
if [ -d "schema" ]; then
    ls -l schema/
else
    echo "❌ CRITICAL: 'schema/' folder is MISSING from $(pwd). This is why tests fail."
fi

echo "--- 🔍 [2/4] SOURCE CONTRACT AUDIT ---"
echo "Line 51 of src/core/state_engine.py (The hydration failure):"
cat -n src/core/state_engine.py | sed -n '45,65p'

echo "Checking LedgerManager.log_scan signature in src/core/update_ledger.py:"
cat -n src/core/update_ledger.py | grep -A 3 "def log_scan"

echo "--- 📜 [3/4] ENV VAR & PATH RECON ---"
echo "PYTHONPATH: $PYTHONPATH"

echo "--- 🔧 [4/4] AUTOMATED REPAIR CANDIDATES (CI-ONLY) ---"
# These 'sed' commands allow you to test fixes without committing to the core repo.
# Copy these into your GitHub Action step before running pytest.

# Fix A: Fix the signature mismatch where tests expect a 'gap' argument but code lacks it.
# sed -i 's/def log_scan(self, project_id, status):/def log_scan(self, project_id, status, gap=None):/' src/core/update_ledger.py

# Fix B: Ensure LedgerManager creates subdirectories for audit logs automatically.
# sed -i '/with open(self.log_path, "w"/i \            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)' src/core/update_ledger.py

# Fix C: Force the schema path to be absolute to prevent CWD-related hydration failures.
# sed -i "s|self.schema_path = 'schema/manifest_schema.json'|self.schema_path = os.path.join(os.path.dirname(__file__), '../../schema/manifest_schema.json')|g" src/core/state_engine.py