FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1 \
    libasound2-dev \
    portaudio19-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel
RUN pip install numpy scipy
RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install chatterbox-tts
RUN pip install jupyter gradio librosa soundfile matplotlib

WORKDIR /workspace
RUN mkdir -p /workspace/models /workspace/audio /workspace/output

COPY process_text.py /workspace/
COPY process_text_enhanced.py /workspace/
COPY process_text_multi_samples.py /workspace/
COPY text_input.txt /workspace/
COPY entrypoint.sh /workspace/
COPY entrypoint_enhanced.sh /workspace/
COPY entrypoint_multi_samples.sh /workspace/
COPY tts_ui.py /workspace/
COPY entrypoint_ui.sh /workspace/
RUN chmod +x /workspace/entrypoint.sh /workspace/entrypoint_enhanced.sh /workspace/entrypoint_multi_samples.sh /workspace/entrypoint_ui.sh

EXPOSE 7860 8888
ENTRYPOINT ["/workspace/entrypoint.sh"]