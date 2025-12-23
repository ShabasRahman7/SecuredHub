"""
Django settings for worker service.
Independent Django project for Celery worker microservice.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
env_path = BASE_DIR.parent.parent / 'infra' / '.env'
if env_path.exists():
    load_dotenv(env_path)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'worker-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'compliance_models',  # Compliance evaluation models (managed=False)
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = None  # Worker doesn't need URL routing

# Database - Shared database with backend
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'secured_hub_db')),
        'USER': os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'secured_hub_user')),
        'PASSWORD': os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', '')),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redis Configuration (supports Upstash)
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# Detect if using Upstash (contains 'upstash' in hostname) - requires TLS
IS_UPSTASH = 'upstash' in REDIS_HOST.lower()

# Build Redis URL for Celery result backend
REDIS_SCHEME = 'rediss' if IS_UPSTASH else 'redis'
REDIS_AUTH = f"default:{REDIS_PASSWORD}@" if REDIS_PASSWORD else ""
redis_location = f"{REDIS_SCHEME}://{REDIS_AUTH}{REDIS_HOST}:{REDIS_PORT}/0"

# For Upstash/TLS, add SSL parameters for Celery
if IS_UPSTASH or REDIS_PASSWORD:
    redis_location_celery = f"{redis_location}?ssl_cert_reqs=CERT_NONE"
else:
    redis_location_celery = redis_location

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672//')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', redis_location_celery)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 50

# Connection retry settings for startup (Celery 6.0+ compatible)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Redis connection retry settings for Upstash
CELERY_REDIS_BACKEND_HEALTH_CHECK_INTERVAL = 25  # Ping every 25 seconds
CELERY_REDIS_SOCKET_CONNECT_TIMEOUT = 5
CELERY_REDIS_SOCKET_TIMEOUT = 5
CELERY_REDIS_RETRY_ON_TIMEOUT = True

# Backend Internal API Configuration
BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://api:8001/api/v1/internal')
INTERNAL_SERVICE_TOKEN = os.getenv('INTERNAL_SERVICE_TOKEN', '')

# Django Channels Configuration (for WebSocket updates)
if IS_UPSTASH or REDIS_PASSWORD:
    # Upstash/authenticated Redis requires URL format with TLS
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [redis_location],
            },
        },
    }
else:
    # Local Redis without authentication
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [(REDIS_HOST, REDIS_PORT)],
            },
        },
    }
