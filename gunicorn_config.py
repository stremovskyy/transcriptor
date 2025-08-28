# gunicorn_config.py
import os

bind = "0.0.0.0:8080"
workers = 1
worker_class = "gthread"
threads = 1
timeout = 500
graceful_timeout = 120
keepalive = 5
# max_requests = 1000
# max_requests_jitter = 5
worker_tmp_dir = "/dev/shm"
preload_app = False

# Environment-aware logging: keep production quiet by default
env = (os.getenv('FLASK_ENV') or os.getenv('APP_ENV') or os.getenv('ENV') or '').lower()
is_prod = env == 'production'

loglevel = os.getenv('GUNICORN_LOG_LEVEL') or ("warning" if is_prod else "info")
# Disable access log in production by default to reduce noise; can be overridden
default_accesslog = None if is_prod else "-"
accesslog = os.getenv('GUNICORN_ACCESSLOG', default_accesslog)
errorlog = os.getenv('GUNICORN_ERRORLOG', "-")
