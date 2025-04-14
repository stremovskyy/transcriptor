# Docker Setup for Audio Transcription & Text Reconstruction Service

This document explains how to run the Audio Transcription & Text Reconstruction Service using Docker with externalized configurations.

## Benefits of Externalized Configurations

Externalizing configurations from the Docker container provides several benefits:

1. **Easy Configuration Updates**: Change configuration files without rebuilding the Docker image
2. **Data Persistence**: Uploaded files and logs persist across container restarts
3. **Model Caching**: Downloaded models are cached locally to avoid re-downloading
4. **Environment-Specific Settings**: Use different environment files for different environments

## Directory Structure

Before running the Docker container, ensure you have the following directory structure:

```
project_root/
├── .env                  # Environment variables
├── logs/                 # Directory for logs (will be created if it doesn't exist)
├── uploads/              # Directory for uploaded files (will be created if it doesn't exist)
├── .cache/               # Directory for model cache (will be created if it doesn't exist)
├── gunicorn_config.py    # Gunicorn configuration
├── docker-compose.yml    # Docker Compose configuration
└── docker_command.sh     # Alternative Docker command script
```

## Using Docker Compose (Recommended)

1. Make sure you have Docker and Docker Compose installed
2. Create the necessary directories:
   ```bash
   mkdir -p logs uploads .cache
   ```
3. Run the service:
   ```bash
   docker-compose up -d
   ```
4. To stop the service:
   ```bash
   docker-compose down
   ```

## Using Docker Command

Alternatively, you can use the provided Docker command script:

1. Make sure you have Docker installed
2. Create the necessary directories:
   ```bash
   mkdir -p logs uploads .cache
   ```
3. Make the script executable:
   ```bash
   chmod +x docker_command.sh
   ```
4. Run the script:
   ```bash
   ./docker_command.sh
   ```
5. To stop the container:
   ```bash
   docker stop whisper-transcription-service
   docker rm whisper-transcription-service
   ```

## Configuration Files

### Environment Variables (.env)

The `.env` file contains environment variables for the application. You can modify this file to change the application's behavior without rebuilding the Docker image.

Key environment variables:
- `FLASK_ENV`: Set to "development" or "production"
- `UPLOAD_FOLDER`: Path to store uploaded files (should be "./uploads" for Docker)
- `API_KEY_ENABLED`: Enable/disable API key authentication
- `API_KEY`: API key for authentication
- `AUDIO_ENABLE_PREPROCESSING`: Enable/disable audio preprocessing

### Gunicorn Configuration (gunicorn_config.py)

The `gunicorn_config.py` file configures the Gunicorn WSGI server. You can modify this file to change server settings without rebuilding the Docker image.

Key settings:
- `workers`: Number of worker processes
- `threads`: Number of threads per worker
- `timeout`: Request timeout in seconds
- `bind`: Address and port to bind to

## GPU Support

If you want to use GPU acceleration, you need to add the `--gpus all` flag to the Docker command or update the docker-compose.yml file to include:

```yaml
services:
  app:
    # ... other settings
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Troubleshooting

If you encounter issues:

1. Check the logs:
   ```bash
   docker logs whisper-transcription-service
   ```
   or
   ```bash
   docker-compose logs
   ```

2. Ensure all directories have the correct permissions:
   ```bash
   chmod -R 777 logs uploads .cache
   ```

3. If models fail to download, check your internet connection and ensure the `.cache` directory is properly mounted.