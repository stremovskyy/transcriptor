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

## Production with Traefik + Autoheal

This repository includes `docker-compose.prod.yml` for a production-ready setup behind Traefik with automatic HTTPS and auto-healing.

1. Prepare env vars:
   - Compose automatically reads variables from a file named `.env` in the working directory.
   - If you keep production values in `.env.prod`, pass it explicitly via `--env-file .env.prod` so variable substitution works for Traefik and labels.
   - Ensure these are defined in whichever env file you use:
   - `DOMAIN` (e.g., `api.example.com`)
   - `TRAEFIK_ACME_EMAIL` (email for Let's Encrypt)

2. Ensure DNS for `DOMAIN` points to your server's public IP.

3. Create required directories for persistence:
   ```bash
   mkdir -p logs uploads
   ```

4. Start Traefik, the app, and autoheal:
   ```bash
   # If using .env.prod
   docker compose --env-file .env.prod -f docker-compose.prod.yml up -d

   # Or if you copied values into .env
   docker compose -f docker-compose.prod.yml up -d
   ```

5. Scale the app horizontally (Traefik load-balances replicas):
   ```bash
   docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --scale transcriptor=3
   ```
   Notes:
   - Scaling requires the service to have no `container_name` (already removed).
   - For GPU workloads, prefer `--scale transcriptor=1` unless you have multiple GPUs.

Replicas in compose file
- The prod compose file sets `deploy.replicas: ${REPLICAS:-3}` for `transcriptor` as a default of 3.
- Docker Compose (non‑Swarm) ignores `deploy.replicas`. To honor replicas in YAML, use Docker Swarm:
  ```bash
  docker swarm init           # once per host
  docker stack deploy -c docker-compose.prod.yml transcriptor
  ```
  With Swarm you can also override at deploy time: `REPLICAS=5 docker stack deploy -c docker-compose.prod.yml transcriptor`.

Make targets (defaults to 3 replicas)
- `make prod-up`: brings up prod with 3 replicas by default. Override with `make prod-up REPLICAS=5`.
- `make prod-down`: stops and removes the prod stack.
- `make prod-logs`: tails prod logs.

5. Access the API over HTTPS at `https://$DOMAIN`.

Notes
- The app's internal healthcheck is exposed at `/health` and used by Docker; containers with label `autoheal=true` are restarted by the autoheal service if they go unhealthy.
- Certificates are stored in the named volume `traefik_letsencrypt`.

Traefik dashboard (secure subdomain)
- Enable dashboard routing is already included in `docker-compose.prod.yml`.
- Set a basic auth user in `.env.prod`:
  ```bash
  # install apache2-utils or httpd-tools on your system to get htpasswd
  htpasswd -nb admin StrongPass
  # copy the output (e.g., admin:$apr1$...$...) into .env.prod
  echo 'TRAEFIK_DASHBOARD_USERS=admin:$apr1$....$....' >> .env.prod
  ```
- Point DNS `traefik.${DOMAIN}` to your server.
- Access the dashboard at: `https://traefik.${DOMAIN}`

Metrics in dashboard
- Prometheus metrics are enabled in Traefik via command flags.
- The dashboard will show metrics after there is some traffic; refresh after a few requests through Traefik.
- If you plan to scrape metrics with Prometheus, either:
  - Run Prometheus in the same Docker network and scrape `http://traefik:9100/metrics`, or
  - Publish port `9100` in `ports:` (uncomment in compose) and scrape externally (recommended to firewall-restrict).
