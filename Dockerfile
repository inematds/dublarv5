# Dublar Pro v4 - Dockerfile com GPU NVIDIA
# Base: NVIDIA PyTorch container (testado com GB10 Blackwell)
FROM nvcr.io/nvidia/pytorch:25.01-py3

WORKDIR /app

# Dependencias de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    rubberband-cli \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python do pipeline
RUN pip install --no-cache-dir \
    faster-whisper>=1.0.0 \
    edge-tts>=6.1.0 \
    bark>=0.1.0 \
    transformers>=4.30.0 \
    sentencepiece>=0.1.99 \
    protobuf>=3.20.0 \
    sacremoses>=0.0.53 \
    httpx>=0.24.0 \
    scipy>=1.10.0 \
    librosa>=0.10.0 \
    soundfile>=0.12.0 \
    yt-dlp>=2023.0.0 \
    Pillow>=10.0.0

# Copiar pipeline
COPY dublar_pro_v4.py .
COPY dublar-pro.sh .

# Diretorios de trabalho e saida
RUN mkdir -p /app/dub_work /app/dublado

ENTRYPOINT ["python", "dublar_pro_v4.py"]
