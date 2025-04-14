# gunicorn_config.py
bind = "0.0.0.0:8080"
workers = 3
worker_class = "gthread"
threads = 4
timeout = 500
graceful_timeout = 120
keepalive = 5
max_requests = 10
max_requests_jitter = 5
worker_tmp_dir = "/dev/shm"
preload_app = True
loglevel = "info"
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
