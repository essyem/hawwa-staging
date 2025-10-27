# Gunicorn configuration for Hawwa Staging
# staging.hawwa.online on port 8003

import multiprocessing

# Server socket
bind = "127.0.0.1:8003"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/root/hawwa/logs/gunicorn_staging_access.log"
errorlog = "/root/hawwa/logs/gunicorn_staging_error.log"
loglevel = "info"
capture_output = True

# Process naming
proc_name = "hawwa_staging"

# Server mechanics
preload_app = True
daemon = False
pidfile = "/root/hawwa/logs/gunicorn_staging.pid"
user = "root"
group = "root"
tmp_upload_dir = None

# SSL (handled by nginx, but keeping options available)
# keyfile = None
# certfile = None