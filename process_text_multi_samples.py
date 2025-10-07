import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
import torch
import os
import re
import librosa
import numpy as np
from pathlib import Path

def clean_text_for_tts(text):
    """Clean and prepare text for TTS processing"""
    # Remove markdown headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Split into sentences for better processing
    sentences = re.split(r'[.!?]+', text)
    
    # Clean and filter sentences
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and len(sentence) > 10:  # Skip very short fragments
            cleaned_sentences.append(sentence + '.')
    
    return cleaned_sentences

def prepare_reference_audio(audio_path, target_sr=24000, max_duration=10.0):
    """Prepare reference audio for voice cloning"""
    if not os.path.exists(audio_path):
        print(f"Reference audio file not found: {audio_path}")
        return None
    
    print(f"Processing reference audio: {audio_path}")
    
    # Load audio
    audio, sr = librosa.load(audio_path, sr=None)
    
    # Trim silence from beginning and end
    audio_trimmed, _ = librosa.effects.trim(audio, top_db=20)
    
    # Limit duration to max_duration seconds for better voice cloning
    max_samples = int(max_duration * sr)
    if len(audio_trimmed) > max_samples:
        audio_trimmed = audio_trimmed[:max_samples]
    
    # Resample to target sample rate if needed
    if sr != target_sr:
        audio_trimmed = librosa.resample(audio_trimmed, orig_sr=sr, target_sr=target_sr)
    
    # Convert to tensor and save processed version
    processed_path = f"/workspace/reference_processed_{Path(audio_path).stem}.wav"
    ta.save(processed_path, torch.from_numpy(audio_trimmed).unsqueeze(0), target_sr)
    
    print(f"Reference audio processed and saved to: {processed_path}")
    print(f"Duration: {len(audio_trimmed) / target_sr:.2f} seconds")
    
    return processed_path

def get_audio_samples():
    """Get all audio files from the audio_samples directory"""
    audio_samples_dir = "/workspace/audio_samples"
    if not os.path.exists(audio_samples_dir):
        print(f"Audio samples directory not found: {audio_samples_dir}")
        return []
    
    # Common audio file extensions
    audio_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.ogg', '.aiff'}
    
    audio_files = []
    for file_path in Path(audio_samples_dir).iterdir():
        if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
            audio_files.append(str(file_path))
    
    return sorted(audio_files)

def process_with_audio_sample(model, sentences, sample_path, sample_name):
    """Process text with a specific audio sample as reference"""
    print(f"\n{'='*60}")
    print(f"Processing with audio sample: {sample_name}")
    print(f"{'='*60}")
    
    # Prepare the reference audio
    reference_audio_path = prepare_reference_audio(sample_path)
    if not reference_audio_path:
        print(f"Failed to process reference audio: {sample_path}")
        return False
    
    # Enhanced TTS parameters for more realistic speech
    tts_params = {
        'repetition_penalty': 1.1,  # Reduce repetitive patterns
        'min_p': 0.02,             # Lower for more natural variation
        'top_p': 0.95,             # Slightly reduce for consistency
        'temperature': 0.7,        # Lower for more stable speech
        'exaggeration': 0.3,       # Lower for more natural prosody
        'cfg_weight': 0.7,         # Higher for better quality
        'audio_prompt_path': reference_audio_path  # Voice cloning
    }
    
    print("TTS Parameters:")
    for key, value in tts_params.items():
        if value is not None:
            print(f"  {key}: {value}")
    
    # Create output directory for this sample
    output_dir = f"/workspace/output/{sample_name}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each sentence
    all_audio = []
    successful_generations = 0
    
    for i, sentence in enumerate(sentences[:25]):  # Process first 25 sentences
        print(f"Processing sentence {i+1}/{min(25, len(sentences))}: {sentence[:60]}...")
        
        try:
            # Generate with enhanced parameters
            wav = model.generate(sentence, **tts_params)
            all_audio.append(wav)
            successful_generations += 1
            
            # Save individual sentence
            output_path = f'{output_dir}/sentence_{i+1:03d}.wav'
            ta.save(output_path, wav, model.sr)
            
        except Exception as e:
            print(f"Error processing sentence {i+1}: {e}")
            continue
    
    # Concatenate all audio
    if all_audio:
        print("Concatenating all audio segments...")
        combined_audio = torch.cat(all_audio, dim=-1)
        complete_output_path = f'{output_dir}/complete_article.wav'
        ta.save(complete_output_path, combined_audio, model.sr)
        print(f"Complete audio saved to {complete_output_path}")
        print(f"Duration: approximately {combined_audio.shape[-1] / model.sr:.1f} seconds")
        print(f"Successfully processed {successful_generations} sentences")
        
        # Clean up processed reference file
        if os.path.exists(reference_audio_path):
            os.remove(reference_audio_path)
        
        return True
    else:
        print("No audio was successfully generated for this sample.")
        return False

def process_text_with_multiple_samples():
    """Main function to process text with multiple audio samples.
    Each run stores results in a unique timestamped directory: /workspace/output/run_<UTC_TS>/sample_name
    Also maintains /workspace/output/latest -> that run (symlink).
    """
    import datetime
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Create a unique run directory
    run_id = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    base_output_dir = f"/workspace/output/run_{run_id}"
    os.makedirs(base_output_dir, exist_ok=True)
    print(f"Run output directory: {base_output_dir}")

    # Update symlink 'latest'
    latest_link = "/workspace/output/latest"
    try:
        if os.path.islink(latest_link) or os.path.exists(latest_link):
            os.unlink(latest_link)
        os.symlink(base_output_dir, latest_link)
        print(f"Updated symlink: {latest_link} -> {base_output_dir}")
    except Exception as e:
        print(f"Could not update latest symlink: {e}")

    # Load the model
    print("Loading Chatterbox TTS model...")
    model = ChatterboxTTS.from_pretrained(device=device)

    # Get all audio samples
    audio_samples = get_audio_samples()
    if not audio_samples:
        print("No audio samples found in /workspace/audio_samples/")
        print("Please add audio files to the audio_samples directory and try again.")
        return

    print(f"Found {len(audio_samples)} audio samples:")
    for sample in audio_samples:
        print(f"  - {Path(sample).name}")

    # Read the input text
    text_file = '/workspace/text_input.txt'
    if not os.path.exists(text_file):
        print(f"Text input file not found: {text_file}")
        return

    with open(text_file, 'r', encoding='utf-8') as f:
        full_text = f.read()

    print(f"Processing text of {len(full_text)} characters...")

    # Clean and split the text
    sentences = clean_text_for_tts(full_text)
    print(f"Split into {len(sentences)} sentences")

    # Process text with each audio sample
    successful_samples = 0
    for sample_path in audio_samples:
        sample_name = Path(sample_path).stem
        try:
            # Patch process_with_audio_sample to accept base directory by temporarily overriding output_dir creation
            # Simpler: replicate call with monkey patched global variable? We just set environment var.
            # We'll adjust by temporarily changing working output inside function via env var.
            # Instead, derive per-sample dir and create before call, then inside function will still use /workspace/output/<sample_name>
            # To avoid collision with older runs, pre-create symlink path to new location.
            target_dir = f"{base_output_dir}/{sample_name}"
            os.makedirs(target_dir, exist_ok=True)
            legacy_path = f"/workspace/output/{sample_name}"
            # If legacy path exists and is not symlink to target_dir, remove/rename
            if os.path.exists(legacy_path) and not os.path.islink(legacy_path):
                try:
                    # Move old directory out of the way
                    backup_dir = f"{legacy_path}_prev_{run_id}"
                    os.rename(legacy_path, backup_dir)
                except Exception:
                    pass
            try:
                if os.path.islink(legacy_path) or os.path.exists(legacy_path):
                    os.unlink(legacy_path)
                os.symlink(target_dir, legacy_path)
            except Exception as e:
                print(f"Warning: could not set symlink for {sample_name}: {e}")
            if process_with_audio_sample(model, sentences, sample_path, sample_name):
                successful_samples += 1
        except Exception as e:
            print(f"Failed to process sample {sample_name}: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Successfully processed {successful_samples}/{len(audio_samples)} audio samples")
    print(f"Run directory: {base_output_dir}")
    print("'latest' symlink points to most recent run.")

    # List all generated files
    print("\nGenerated output structure:")
    import subprocess
    result = subprocess.run(['find', base_output_dir, '-name', '*.wav'], capture_output=True, text=True)
    if result.stdout:
        for line in sorted(result.stdout.strip().split('\n')):
            print(f"  {line}")

if __name__ == "__main__":
    process_text_with_multiple_samples()