import multiprocessing
import os

DEFAULT_WORKERS = multiprocessing.cpu_count() * 2 + 1

port = os.getenv("HTTP_PORT")
bind = f"0.0.0.0:{port}"
workers = os.getenv("WORKERS")
workers = int(workers) if workers else DEFAULT_WORKERS
worker_class = "uvicorn.workers.UvicornWorker"
