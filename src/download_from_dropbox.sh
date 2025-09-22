#!/bin/bash

APP_KEY="${APP_KEY}"
APP_SECRET="${APP_SECRET}"
REFRESH_TOKEN="${REFRESH_TOKEN}"
DROPBOX_FOLDER="/engineering_simulations_pipeline"
LOCAL_FOLDER="./data/testing-input-output"
LOG_FILE="./dropbox_download_log.txt"

mkdir -p "$LOCAL_FOLDER"

echo "📥 Downloading files from Dropbox..."
python3 src/download_dropbox_files.py download "$DROPBOX_FOLDER" "$LOCAL_FOLDER" "$REFRESH_TOKEN" "$APP_KEY" "$APP_SECRET" "$LOG_FILE"

if [ "$(ls -A "$LOCAL_FOLDER")" ]; then
  echo "✅ Files successfully downloaded to $LOCAL_FOLDER"
else
  echo "❌ ERROR: No files were downloaded from Dropbox. Check your credentials and folder path."
  exit 1
fi



