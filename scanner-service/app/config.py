"""
Scanner Service Configuration
"""
import os
from celery import Celery

# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672//')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://secured_hub_user:StrongPassword123@db:5432/secured_hub_db')

# Scanner configuration
SCANNER_WORKSPACE = os.getenv('SCANNER_WORKSPACE', '/tmp/scanner_workspace')
SCANNER_TIMEOUT = int(os.getenv('SCANNER_TIMEOUT', '600'))  # 10 minutes

# Celery app
app = Celery('scanner_service')
app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
