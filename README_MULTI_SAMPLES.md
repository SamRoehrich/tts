# TTS Multi-Sample Processing

This system generates TTS output using multiple audio samples as voice references.

## Setup

1. **Add your audio samples**: Place your audio files in the `audio_samples/` directory
   - Supported formats: `.wav`, `.mp3`, `.flac`, `.m4a`, `.ogg`, `.aiff`
   - Each audio file will be used as a voice reference
   - Audio files should be good quality recordings of speech (ideally 5-10 seconds)

2. **Add your text**: Put the text you want to convert to speech in `text_input.txt`

## Usage

### Multi-Sample Processing (NEW)
```bash
# Process text with all audio samples in audio_samples/ directory
docker-compose up chatterbox-tts-multi
```

This will:
- Find all audio files in `audio_samples/`
- For each audio file, generate TTS output using that file as the voice reference
- Create organized output directories: `output/{sample_name}/`
- Generate both individual sentence files and complete audio files

### Original Single-Sample Processing
```bash
# Process with enhanced settings (looks for reference.wav)
docker-compose up chatterbox-tts
```

## Output Structure

After running multi-sample processing, your output will be organized like this:

```
output/
├── sample1/
│   ├── sentence_001.wav
│   ├── sentence_002.wav
│   ├── ...
│   └── complete_article.wav
├── sample2/
│   ├── sentence_001.wav
│   ├── sentence_002.wav
│   ├── ...
│   └── complete_article.wav
└── ...
```

Each directory contains:
- Individual sentence files (`sentence_XXX.wav`)
- Complete article file (`complete_article.wav`)

## Example Workflow

1. **Prepare audio samples**:
   ```bash
   # Add your voice samples
   cp /path/to/voice1.wav audio_samples/
   cp /path/to/voice2.mp3 audio_samples/
   cp /path/to/voice3.flac audio_samples/
   ```

2. **Add your text**:
   ```bash
   echo "Your text content here..." > text_input.txt
   ```

3. **Run processing**:
   ```bash
   docker-compose up chatterbox-tts-multi
   ```

4. **Check results**:
   ```bash
   ls -la output/
   # Will show directories named after your audio samples
   ```

## Tips

- **Audio Quality**: Use clear, high-quality audio samples for best results
- **Sample Length**: 5-10 second samples work well for voice cloning
- **Multiple Voices**: Add as many different voice samples as you want - each will generate a complete output
- **File Naming**: Output directories are named after your audio sample files (without extension)

## Troubleshooting

- **No audio samples found**: Make sure files are in the `audio_samples/` directory
- **Poor voice cloning**: Try using higher quality, longer audio samples
- **GPU errors**: Ensure NVIDIA drivers and Docker GPU support are properly configured