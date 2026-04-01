#!/bin/bash
# src/debug/forensic_audit.sh

echo "🔍 ARCHIVIST I/O: SYSTEM FORENSIC AUDIT"
echo "----------------------------------------"

# 1. Check Configuration
if [ -f "config/active_disk.json" ]; then
    PROJECT_ID=$(grep -o '"project_id": "[^"]*' config/active_disk.json | cut -d'"' -f4)
    echo "✅ Active Disk Found: $PROJECT_ID"
else
    echo "❌ CRITICAL: No active_disk.json found in /config"
    exit 1
fi

# 2. Check Schema
if [ -f "config/core_schema.json" ]; then
    echo "✅ Sovereign Schema Present."
else
    echo "❌ CRITICAL: core_schema.json missing!"
fi

# 3. Data Integrity Scan
echo "📂 Scanning /data/testing-input-output..."
FILES_COUNT=$(ls -1 data/testing-input-output | wc -l)

if [ "$FILES_COUNT" -eq 0 ]; then
    echo "⚠️  Data Directory is EMPTY. Engine will default to initial ingestion."
else
    echo "📄 Found $FILES_COUNT artifacts. Ready for Forensic Scan."
fi

echo "----------------------------------------"
echo "🏁 Audit Complete."