#!/bin/bash
# src/debug/forensic_audit.sh

DATA_DIR="data/testing-input-output"

echo "🔍 FORENSIC DISCOVERY: PHYSICAL FOLDER AUDIT"
echo "--------------------------------------------"

if [ -f "$DATA_DIR/results.zip" ]; then
    echo "🏁 STATE: COMPLETE. (results.zip detected)"
elif [ -f "$DATA_DIR/geometry.msh" ]; then
    echo "⚙️  STATE: READY FOR PHYSICS. (geometry.msh detected)"
elif [ -f "$DATA_DIR/fluid_simulation_input.json" ]; then
    echo "⚡ STATE: READY FOR INITIAL STEP. (input detected)"
else
    echo "🌑 STATE: EMPTY. (No artifacts found)"
fi

echo "--------------------------------------------"
ls -F $DATA_DIR