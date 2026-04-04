#!/bin/bash
# --- FORENSIC AUDIT: BOOTLOADER HYDRATION & DEPENDENCY MAPPING ---

echo "🔍 STAGE 1: Dependency Inventory"
pip list | grep -E "responses|requests|pytest" || echo "❌ MISSING: 'responses' library not found in environment."

echo -e "\n🔍 STAGE 2: Source Code Audit (Smoking Gun Lines)"
# Audit the Bootloader for Hydration logic (Lines 63-133)
cat -n src/core/bootloader.py | sed -n '63,133p'

# Audit the State Engine for Persistence and Transitions (Lines 110-166)
cat -n src/core/state_engine.py | sed -n '110,166p'

echo -e "\n🔍 STAGE 3: Path and Environment Validation"
echo "Current Directory: $(pwd)"
echo "Python Path: $PYTHONPATH"
ls -R tests/core/

echo -e "\n🛠️ STAGE 4: Automated Repair Proposals (Draft)"
# To fix the CI, add 'responses' to your requirements or install it directly:
# pip install responses

# Proposed sed injection for State Engine Persistence logging fix
# sed -i '114s/logger.error(f"❌ Persistence Error: Failed to write ledger. {e}")/logger.error(f"❌ Persistence Error | {type(e).__name__}: {e}")/' src/core/state_engine.py

# Proposed sed injection for Bootloader OS resilience
# sed -i '53s/logger.error(f"Failed to reset dormancy flag: {e}")/logger.warning(f"⚠️ Dormancy Reset Skipped: {e}")/' src/core/bootloader.py

echo -e "\n✅ Audit Complete."