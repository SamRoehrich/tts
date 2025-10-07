import os
import gradio as gr
import torch
import torchaudio as ta
import tempfile
import time
from datetime import datetime
from pathlib import Path
from chatterbox.tts import ChatterboxTTS
import librosa
import numpy as np

MODEL_CACHE = {}

def get_model(device):
    if 'model' not in MODEL_CACHE:
        MODEL_CACHE['model'] = ChatterboxTTS.from_pretrained(device=device)
    return MODEL_CACHE['model']


def prepare_reference(audio_file, target_sr=24000, max_duration=12.0):
    if not audio_file:
        return None, None
    try:
        y, sr = librosa.load(audio_file, sr=None)
        y_trim, _ = librosa.effects.trim(y, top_db=25)
        max_samples = int(max_duration * sr)
        if len(y_trim) > max_samples:
            y_trim = y_trim[:max_samples]
        if sr != target_sr:
            y_trim = librosa.resample(y_trim, orig_sr=sr, target_sr=target_sr)
        ref_path = Path(tempfile.gettempdir()) / f"ref_{int(time.time()*1000)}.wav"
        ta.save(str(ref_path), torch.from_numpy(y_trim).unsqueeze(0), target_sr)
        return str(ref_path), f"Reference OK. Duration: {len(y_trim)/target_sr:.2f}s"
    except Exception as e:
        return None, f"Reference processing failed: {e}"


def generate_tts(text, reference_audio, repetition_penalty, min_p, top_p, temperature, exaggeration, cfg_weight, sentence_limit, device_select):
    device = device_select if device_select in ("cuda", "cpu") else ("cuda" if torch.cuda.is_available() else "cpu")
    model = get_model(device)

    if not text or len(text.strip()) < 2:
        return None, "Provide some input text.", None

    # Basic sentence splitting (reuse simple logic)
    import re
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip()+'.' for s in sentences if s.strip()]
    if sentence_limit:
        sentences = sentences[:sentence_limit]

    # Reference audio
    ref_path = None
    ref_status = "Using default voice (no reference provided)."
    if reference_audio is not None:
        ref_path, ref_status = prepare_reference(reference_audio)

    params = dict(
        repetition_penalty=repetition_penalty,
        min_p=min_p,
        top_p=top_p,
        temperature=temperature,
        exaggeration=exaggeration,
        cfg_weight=cfg_weight,
        audio_prompt_path=ref_path
    )

    all_audio = []
    sr = model.sr
    logs = [f"Device: {device}", ref_status, f"Sentences: {len(sentences)}"]
    for i, sent in enumerate(sentences, 1):
        try:
            wav = model.generate(sent, **params)
            all_audio.append(wav)
            logs.append(f"[OK] {i}: {sent[:60]}")
        except Exception as e:
            logs.append(f"[ERR] {i}: {e}")

    if not all_audio:
        return None, "No audio generated.\n" + '\n'.join(logs), '\n'.join(logs)

    combined = torch.cat(all_audio, dim=-1)
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    run_dir = Path('/workspace/output/ui_runs/run_' + ts)
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / 'complete_article.wav'
    ta.save(str(out_path), combined, sr)

    # Provide logs and path listing
    listing = []
    for p in run_dir.glob('*.wav'):
        listing.append(str(p))
    logs.append(f"Saved: {out_path}")
    return str(out_path), '\n'.join(logs), '\n'.join(listing)

with gr.Blocks(title="Chatterbox Multi-Voice TTS") as demo:
    gr.Markdown("# Chatterbox Multi-Voice TTS\nUpload a reference voice (optional) and generate speech from text. Tune parameters for experimentation.")

    with gr.Row():
        with gr.Column(scale=2):
            text_input = gr.Textbox(label="Input Text", lines=8, placeholder="Paste text to synthesize...")
            reference_audio = gr.Audio(label="Reference Voice (optional)", type="filepath")
            sentence_limit = gr.Slider(1, 50, value=25, step=1, label="Sentence Limit")
            device_select = gr.Radio(["auto", "cpu", "cuda"], value="auto", label="Device")
            run_btn = gr.Button("Generate", variant="primary")

        with gr.Column():
            gr.Markdown("### TTS Parameters")
            repetition_penalty = gr.Slider(0.8, 2.0, value=1.1, step=0.05, label="Repetition Penalty")
            min_p = gr.Slider(0.0, 0.2, value=0.02, step=0.005, label="Min P")
            top_p = gr.Slider(0.5, 1.0, value=0.95, step=0.01, label="Top P")
            temperature = gr.Slider(0.1, 1.5, value=0.7, step=0.05, label="Temperature")
            exaggeration = gr.Slider(0.0, 1.0, value=0.3, step=0.05, label="Exaggeration")
            cfg_weight = gr.Slider(0.0, 2.0, value=0.7, step=0.05, label="CFG Weight")

    with gr.Row():
        output_audio = gr.Audio(label="Generated Audio", type="filepath")
        log_box = gr.Textbox(label="Logs", lines=14)
        file_list = gr.Textbox(label="Run Files", lines=14)

    run_btn.click(
        fn=generate_tts,
        inputs=[text_input, reference_audio, repetition_penalty, min_p, top_p, temperature, exaggeration, cfg_weight, sentence_limit, device_select],
        outputs=[output_audio, log_box, file_list]
    )

if __name__ == "__main__":
    # Bind to 0.0.0.0 for tailnet exposure
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True)