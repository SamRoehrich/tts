#!/bin/bash

echo "Enhanced Chatterbox TTS Docker Container - Voice Cloning & Realistic Speech"
echo "========================================================================="

echo ""
echo "GPU Status:"
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name --format=csv,noheader | head -1
else
    echo "No GPU detected - using CPU"
fi

echo ""
echo "Checking for reference audio files..."
reference_found=false
for file in reference.wav reference.mp3 reference.m4a reference_audio.wav voice_sample.wav; do
    if [ -f "/workspace/$file" ]; then
        echo "Found reference audio: $file"
        reference_found=true
        break
    fi
done

if [ "$reference_found" = false ]; then
    echo "No reference audio found for voice cloning."
    echo "To enable voice cloning, mount a reference audio file as:"
    echo "  - reference.wav, reference.mp3, reference.m4a, or voice_sample.wav"
fi

echo ""
echo "Starting enhanced text-to-speech processing..."
cd /workspace

if [ -f "process_text_enhanced.py" ]; then
    python process_text_enhanced.py
else
    echo "Enhanced script not found, using standard script..."
    python process_text.py
fi

echo ""
echo "Available commands:"
echo "  - To run Jupyter: jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root"
echo "  - To run Gradio demo: python -c \"from chatterbox.tts import ChatterboxTTS; ChatterboxTTS.demo()\""
echo ""
echo "Keep container running for interactive use..."
tail -f /dev/null