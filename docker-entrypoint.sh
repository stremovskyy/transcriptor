#!/usr/bin/env sh
set -e

# Ensure cache directories exist and are writable by appuser
mkdir -p /home/appuser/.cache/whisper \
         /home/appuser/.cache/torch \
         /home/appuser/.cache/torch/hub \
         /home/appuser/.cache/torch/hub/checkpoints

# Fix ownership in case named volumes created with root ownership
chown -R appuser:appuser /home/appuser/.cache || true
chown -R appuser:appuser /app/uploads || true

exec gosu appuser:appuser "$@"

