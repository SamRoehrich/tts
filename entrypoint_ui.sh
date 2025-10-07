#!/bin/bash
set -e

echo "Starting Chatterbox TTS UI..."
mkdir -p /workspace/output/ui_runs
# Allow running as non-root mapped user
chmod -R a+rw /workspace/output || true

python3 /workspace/tts_ui.py