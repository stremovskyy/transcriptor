#!/bin/bash

# Build the Docker image
docker build -t whisper-transcription-service .

# Run the container with all configurations externalized
docker run -d \
  --gpus all \
  --name whisper-transcription-service \
  -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/gunicorn_config.py:/app/gunicorn_config.py \
  -v $(pwd)/.cache:/home/appuser/.cache \
  --restart always \
  whisper-transcription-service