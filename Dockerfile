FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    YOLO_CONFIG_DIR=/tmp/Ultralytics \
    PORT=7860

WORKDIR /app

RUN mkdir -p /tmp/Ultralytics

# OpenCV runtime libraries.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Ensure Depth-Anything-V2 code and vits checkpoint are present in cloud builds.
RUN if [ ! -d "/app/Depth-Anything-V2/depth_anything_v2" ]; then \
            git clone --depth 1 https://github.com/DepthAnything/Depth-Anything-V2.git /app/Depth-Anything-V2; \
        fi \
        && mkdir -p /app/Depth-Anything-V2/checkpoints \
        && if [ ! -f "/app/Depth-Anything-V2/checkpoints/depth_anything_v2_vits.pth" ]; then \
            curl -L "https://huggingface.co/depth-anything/Depth-Anything-V2-Small/resolve/main/depth_anything_v2_vits.pth?download=true" \
            -o /app/Depth-Anything-V2/checkpoints/depth_anything_v2_vits.pth; \
        fi

EXPOSE 7860

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-7860}"]
