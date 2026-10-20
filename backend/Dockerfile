# syntax=docker/dockerfile:1.7
# GlowMatch API — FastAPI + PyTorch CPU.
# Artefak model TIDAK di-bake ke image (besar & sebagian gated); di-mount sebagai volume:
#   /app/models/undertone   artefak Kaggle modul undertone   (hasil extract_models.py collect/repack)
#   /app/models/season      artefak Kaggle modul season
#   /app/models/hf_cache    bobot pretrained Hugging Face     (hasil extract_models.py fetch)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# PyTorch CPU-only lebih dulu (layer terbesar, jarang berubah). Ganti TORCH_INDEX ke .../whl/cu124 untuk GPU.
ARG TORCH_INDEX=https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --index-url ${TORCH_INDEX} torch torchvision \
    && pip install -r requirements.txt

# Detektor wajah YuNet (OpenCV Zoo, publik, ~230 KB) — dikunci dengan checksum.
ADD --checksum=sha256:8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4 \
    https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx \
    /app/models/face_detection_yunet_2023mar.onnx

COPY app ./app
COPY ml ./ml
COPY scripts/extract_models.py ./scripts/extract_models.py
COPY models/manifest.json ./models/manifest.json

RUN useradd --create-home --uid 10001 glowmatch \
    && mkdir -p /app/models/undertone /app/models/season /app/models/hf_cache \
    && chown -R glowmatch:glowmatch /app
USER glowmatch

ENV GLOWMATCH_MODELS_DIR=/app/models \
    GLOWMATCH_DEVICE=cpu \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

EXPOSE 8000
# Liveness saja: API tetap hidup (status "degraded") walau model gagal dimuat; lihat /api/health.
HEALTHCHECK --interval=30s --timeout=5s --start-period=240s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)" || exit 1

# 1 worker: tiap worker memuat seluruh model (~2-3 GB RAM). Skala horizontal dengan menambah replika.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
