import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
import torch
import os
import re

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

def process_long_text():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Load the model
    print("Loading Chatterbox TTS model...")
    model = ChatterboxTTS.from_pretrained(device=device)
    
    # Read the input text
    with open('/workspace/text_input.txt', 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    print(f"Processing text of {len(full_text)} characters...")
    
    # Clean and split the text
    sentences = clean_text_for_tts(full_text)
    print(f"Split into {len(sentences)} sentences")
    
    # Process each sentence
    all_audio = []
    
    for i, sentence in enumerate(sentences[:25]):  # Process first 25 sentences
        print(f"Processing sentence {i+1}/{min(25, len(sentences))}: {sentence[:60]}...")
        
        try:
            wav = model.generate(sentence)
            all_audio.append(wav)
            
            # Save individual sentence
            output_path = f'/workspace/output/sentence_{i+1:03d}.wav'
            ta.save(output_path, wav, model.sr)
            
        except Exception as e:
            print(f"Error processing sentence {i+1}: {e}")
            continue
    
    # Concatenate all audio
    if all_audio:
        print("Concatenating all audio segments...")
        combined_audio = torch.cat(all_audio, dim=-1)
        ta.save('/workspace/output/complete_article.wav', combined_audio, model.sr)
        print(f"Complete audio saved to /workspace/output/complete_article.wav")
        print(f"Duration: approximately {combined_audio.shape[-1] / model.sr:.1f} seconds")
    
    print("Text processing complete!")
    print("Generated files:")
    import subprocess
    result = subprocess.run(['ls', '-la', '/workspace/output'], capture_output=True, text=True)
    print(result.stdout)

if __name__ == "__main__":
    process_long_text()