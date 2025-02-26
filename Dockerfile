# Build Stage
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Stage
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    UPLOAD_FOLDER=/app/uploads \
    PATH="/home/appuser/.local/bin:$PATH"

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/uploads && \
    adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser app app
COPY --chown=appuser:appuser gunicorn_config.py .
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser run.py .

# Expose the Flask application port
EXPOSE 8080

# Switch to non-root user
USER appuser

# Set health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8080/ || exit 1

# Run the application
CMD ["gunicorn", "-c", "/app/gunicorn_config.py", "run:app"]