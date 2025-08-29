FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    UPLOAD_FOLDER=/app/uploads \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps
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
COPY requirements.txt ./
# Install PyTorch ecosystem explicitly to ensure CUDA 12.1 wheels, then the rest
RUN pip install --no-cache-dir --no-compile --index-url https://download.pytorch.org/whl/cu121 \
      torchaudio==2.3.1 && \
    grep -vE "^(torch|torchaudio)$" requirements.txt > requirements.npt.txt && \
    pip install --no-cache-dir --no-compile -r requirements.npt.txt && \
    rm -f requirements.npt.txt

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
