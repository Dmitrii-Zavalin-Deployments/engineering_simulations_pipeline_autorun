#!/bin/bash
# src/debug/forensic_audit.sh
# Purpose: Final Resolution for Bootloader Auto-Wake Logic Disconnect

echo "============================================================"
echo "🛰️ SMOKING GUN: Internal Path Resolution (src/core/bootloader.py)"
echo "Checking how the Bootloader derives the dormant flag path..."
echo "============================================================"
# We need to see if it's using hardcoded names or dynamic path joining
cat -n src/core/bootloader.py | grep -C 5 "dormant_flag ="

echo -e "\n============================================================"
echo "🔍 DIAGNOSTIC: File System Search"
echo "Searching for any 'dormant.flag' files created during tests..."
echo "============================================================"
# If this returns more than one path, we've found the shadow file.
find /tmp -name "dormant.flag" 2>/dev/null

echo -e "\n============================================================"
echo "🛠️ PROPOSED ATOMIC REPAIRS"
echo "============================================================"

# REPAIR 1: Force Logic Resilience (Greater-Than-Or-Equal)
# Ensures CI timestamp collisions don't stall the boot sequence.
# sed -i '49s/>/>=/' src/core/bootloader.py

# REPAIR 2: Path Alignment (The "Nomadic Node" Fix)
# Ensures the Bootloader uses the directory of the config_path passed to it.
# sed -i "s/dormant_flag = Path(\"dormant.flag\")/dormant_flag = Path(config_path).parent \/ \"dormant.flag\"/" src/core/bootloader.py

# REPAIR 3: Test Assertion Alignment
# Updates the test to be more descriptive if the failure persists.
# sed -i 's/assert "ACTIVE" in content/assert "ACTIVE" in content, f"Node Mismatch: {dormant_path} stayed DORMANT"/' tests/behavior/test_boot_sequence.py

echo -e "\n✅ Forensic Audit Complete. Review the 'find' results above."
echo "If two dormant.flag files exist, Repair 2 is your priority."