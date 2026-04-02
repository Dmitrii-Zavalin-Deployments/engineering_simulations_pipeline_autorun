#!/bin/bash
echo "🔍 STARTING DEEP FORENSIC AUDIT: Phase C Integrity Check"
echo "=========================================================="

# 1. DIAGNOSE: Locate the TypeError smoking guns in tests
echo "📍 [DIAGNOSTIC] Locating outdated test calls to forensic_artifact_scan:"
grep -r "forensic_artifact_scan()" tests/

# 2. DIAGNOSE: Audit the Rule 4 Violation in update_ledger.py
echo -e "\n📍 [DIAGNOSTIC] Examining src/core/update_ledger.py for Rule 4 violations:"
cat -n src/core/update_ledger.py | grep ".get("

# 3. ROOT CAUSE: Inspect the state_engine definition vs test calls
echo -e "\n📍 [DIAGNOSTIC] Signature Mismatch Audit:"
echo "Engine Definition:"
grep "def forensic_artifact_scan" src/core/state_engine.py
echo "Test Implementation Example (test_integration_gate.py):"
sed -n '70p' tests/test_integration_gate.py

# 4. AUTOMATED REPAIR SCRIPTS (Commented - Remove # to apply)
echo -e "\n🛠️ [REPAIR] Prepared Injections for Sovereignty Alignment:"

# Repair Rule 4 Violation in update_ledger.py (Removing .get fallback)
# sed -i 's/metadata.get("timeout_hours", 6)/metadata["timeout_hours"]/g' src/core/update_ledger.py

# Update Tests to pass an empty ledger {} as a baseline for legacy tests
# sed -i 's/forensic_artifact_scan()/forensic_artifact_scan({})/g' tests/test_integration_gate.py
# sed -i 's/forensic_artifact_scan()/forensic_artifact_scan({})/g' tests/core/test_forensic_logic.py
# sed -i 's/forensic_artifact_scan()/forensic_artifact_scan({})/g' tests/core/test_future_proof.py

echo "=========================================================="
echo "✅ FORENSIC AUDIT COMPLETE: Proceed with manual or sed repairs."