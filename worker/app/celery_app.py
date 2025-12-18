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
    task_routes={
        "worker.tasks.*": {"queue": "scans"},
        "scans.tasks.*": {"queue": "scans"},
    },
)

# Only load tasks from the worker app; the scans module here only defines models.
app.autodiscover_tasks(["app"])
