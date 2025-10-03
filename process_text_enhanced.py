import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
import torch
import os
import re
import librosa
import numpy as np

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
    processed_path = "/workspace/reference_processed.wav"
    ta.save(processed_path, torch.from_numpy(audio_trimmed).unsqueeze(0), target_sr)
    
    print(f"Reference audio processed and saved to: {processed_path}")
    print(f"Duration: {len(audio_trimmed) / target_sr:.2f} seconds")
    
    return processed_path

def process_long_text_enhanced():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Load the model
    print("Loading Chatterbox TTS model...")
    model = ChatterboxTTS.from_pretrained(device=device)
    
    # Check for reference audio
    reference_audio_path = None
    possible_ref_paths = [
        "/workspace/reference.wav",
        "/workspace/reference.mp3", 
        "/workspace/reference.m4a",
        "/workspace/reference_audio.wav",
        "/workspace/voice_sample.wav"
    ]
    
    for path in possible_ref_paths:
        if os.path.exists(path):
            reference_audio_path = prepare_reference_audio(path)
            break
    
    if reference_audio_path:
        print(f"Using reference audio for voice cloning: {reference_audio_path}")
    else:
        print("No reference audio found. Using default voice.")
        print("To use voice cloning, place your reference audio file as 'reference.wav' in the workspace.")
    
    # Read the input text
    with open('/workspace/text_input.txt', 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    print(f"Processing text of {len(full_text)} characters...")
    
    # Clean and split the text
    sentences = clean_text_for_tts(full_text)
    print(f"Split into {len(sentences)} sentences")
    
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
            output_path = f'/workspace/output/enhanced_sentence_{i+1:03d}.wav'
            ta.save(output_path, wav, model.sr)
            
        except Exception as e:
            print(f"Error processing sentence {i+1}: {e}")
            continue
    
    # Concatenate all audio
    if all_audio:
        print("Concatenating all audio segments...")
        combined_audio = torch.cat(all_audio, dim=-1)
        ta.save('/workspace/output/enhanced_complete_article.wav', combined_audio, model.sr)
        print(f"Enhanced complete audio saved to /workspace/output/enhanced_complete_article.wav")
        print(f"Duration: approximately {combined_audio.shape[-1] / model.sr:.1f} seconds")
        print(f"Successfully processed {successful_generations} sentences")
    
    print("Enhanced text processing complete!")
    print("Generated files:")
    import subprocess
    result = subprocess.run(['ls', '-la', '/workspace/output'], capture_output=True, text=True)
    print(result.stdout)

if __name__ == "__main__":
    process_long_text_enhanced()