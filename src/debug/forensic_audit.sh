#!/bin/bash
# ------------------------------------------------------------------------------
# ARCHIVE-DRIVEN SIMULATION ENGINE: PHYSICAL-TRUTH ENFORCEMENT
# Target: src/core/state_engine.py (forensic_artifact_scan)
# ------------------------------------------------------------------------------

echo "🔍 INITIATING DEEP LOGIC REPAIR..."
echo "========================================================================"

## 1. SMOKING-GUN: Missing Path validation in the loop
# We need to inject a check that verifies if 'produces' files exist 
# for steps the ledger thinks are 'COMPLETED'.

sed -i '85i \        from pathlib import Path' src/core/state_engine.py

# Inject the forensic gate inside the loop (around line 86-90)
# This logic ensures that if a step is marked COMPLETED but files are missing,
# we return the step as "Ready for Re-run" or halt the scan.

sed -i '/for step in self.manifest_data\["pipeline_steps"\]:/a \            job_name = step["name"]\n            status = orchestration_ledger.get(job_name, {}).get("status", "PENDING")\n            \n            # PHYSICAL TRUTH CHECK\n            all_outputs_present = all(Path(self.data_path) / f).exists() for f in step.get("produces", []))\n            \n            if status == "COMPLETED" and not all_outputs_present:\n                logger.error(f"❌ ARTIFACT GAP: [{job_name}] marked COMPLETED but outputs missing.")\n                return [step]  # Force return this step as the current blockage' src/core/state_engine.py

## 2. GLOBAL CLEANUP
echo "🧹 Cleaning up double-negative logic..."
sed -i 's/if not all_outputs_present == True/if not all_outputs_present/g' src/core/state_engine.py

echo "🛠️  Verification pass..."
echo "========================================================================"

## 3. FINAL VERIFICATION
echo "📊 LOGIC PREVIEW (The Forensic Gate):"
cat -n src/core/state_engine.py | sed -n '85,100p'

# Verify the test now passes
if command -v pytest > /dev/null; then
    echo "Running verification: test_scenario_blocked_step..."
    # Note: We expect this to return the list with the step, 
    # matching the test's expectation of how the engine identifies the blockage.
    pytest tests/behavior/test_forensic_behavior.py::test_scenario_blocked_step
fi

exit 0