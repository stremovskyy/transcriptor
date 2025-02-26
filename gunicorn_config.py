# gunicorn_config.py
bind = "0.0.0.0:8080"
workers = 2
timeout = 120
loglevel = "info"
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"