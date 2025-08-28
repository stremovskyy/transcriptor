# Build Stage
FROM python:3.10-slim AS builder
WORKDIR /app
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libsndfile1 ffmpeg \
 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
# Install CUDA-enabled PyTorch (bundled CUDA 12.1)
RUN pip install --no-cache-dir --no-compile --user \
      --index-url https://download.pytorch.org/whl/cu121 \
      torch==2.3.1 && \
    # Install remaining Python dependencies
    pip install --no-cache-dir --no-compile --user -r requirements.txt

# Final Stage
FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    UPLOAD_FOLDER=/app/uploads \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/appuser/.local/bin:$PATH"
WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg libsndfile1 curl gosu \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/logs /app/uploads && \
    adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

# Ensure cache dirs exist for shared volumes
RUN mkdir -p /home/appuser/.cache/whisper /home/appuser/.cache/torch && \
    chown -R appuser:appuser /home/appuser/.cache

# Python deps
COPY --from=builder /root/.local /home/appuser/.local

# App
COPY --chown=appuser:appuser app app
COPY --chown=appuser:appuser gunicorn_config.py .
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser run.py .
COPY --chown=appuser:appuser .env.example .
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8080
USER root

HEALTHCHECK --interval=60s --timeout=15s --start-period=30s --retries=3 \
  CMD curl -fsS http://localhost:8080/health || exit 1

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["gunicorn", "-c", "/app/gunicorn_config.py", "run:app"]
