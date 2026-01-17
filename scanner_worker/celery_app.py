import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

app = Celery('scanner_worker')

app.set_default()
app.fixups = []

broker_url = os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672//')
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = os.getenv('REDIS_PORT', '6379')
redis_password = os.getenv('REDIS_PASSWORD', '')

is_upstash = 'upstash' in redis_host.lower()
redis_scheme = 'rediss' if is_upstash else 'redis'
redis_auth = f"default:{redis_password}@" if redis_password else ""
result_backend = f"{redis_scheme}://{redis_auth}{redis_host}:{redis_port}/0"

if is_upstash:
    result_backend += "?ssl_cert_reqs=none"

app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    broker_transport_options={
        'socket_keepalive': True,
        'socket_connect_timeout': 30,
        'retry_on_timeout': True,
    },
    redis_socket_keepalive=True,
    redis_socket_connect_timeout=30,
    redis_retry_on_timeout=True,
    result_backend_transport_options={
        'socket_keepalive': True,
        'socket_connect_timeout': 30,
        'retry_on_timeout': True,
        'health_check_interval': 25,
    },
)

import tasks  # noqa
