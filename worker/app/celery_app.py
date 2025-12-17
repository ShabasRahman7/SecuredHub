import os
import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))
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

app.autodiscover_tasks(["app", "scans"])
