#!/bin/bash

echo "Starting Chatterbox TTS Multi-Sample Processing..."
echo "Checking for audio samples in /workspace/audio_samples..."

if [ ! -d "/workspace/audio_samples" ] || [ -z "$(ls -A /workspace/audio_samples 2>/dev/null)" ]; then
    echo "No audio samples found in /workspace/audio_samples/"
    echo "Please add your audio sample files to the audio_samples directory"
    echo "Supported formats: .wav, .mp3, .flac, .m4a, .ogg, .aiff"
    exit 1
fi

echo "Found audio samples:"
ls -la /workspace/audio_samples/

echo "Starting processing with multiple audio samples..."
python3 /workspace/process_text_multi_samples.py

echo "Processing complete! Check /workspace/output/ for results organized by sample name."