#!/bin/bash

echo "Chatterbox TTS Docker Container - Text Processing"
echo "==============================================="
echo ""
echo "GPU Status:"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits 2>/dev/null || echo "No GPU detected - using CPU"
echo ""

if [ $# -eq 0 ]; then
    echo "Processing the Death on Shishapangma article..."
    python process_text.py
    echo ""
    echo "Audio files generated in /workspace/output/"
    ls -la /workspace/output/
else
    exec "$@"
fi