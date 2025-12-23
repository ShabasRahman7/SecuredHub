import os

# Point Celery at the worker's dedicated Django settings module.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from django.conf import settings
from celery import Celery

app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    redis_backend_health_check_interval=25,
    redis_socket_connect_timeout=5,
    redis_socket_timeout=5,
    redis_retry_on_timeout=True,
    task_routes={
        "compliance.tasks.*": {"queue": "compliance"},
    },
)

# Autodiscover tasks from compliance module
app.autodiscover_tasks(["compliance"])
