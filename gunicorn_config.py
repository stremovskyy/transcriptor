# gunicorn_config.py
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
loglevel = "info"
accesslog = "-"
errorlog = "-"
