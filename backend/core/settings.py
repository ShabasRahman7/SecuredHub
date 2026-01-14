# django models/views/serializers

import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

# building paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# loading environment variables
# try loading from backend/.env first, then fallback to infra/.env
env_path = BASE_DIR / '.env'
if not env_path.exists():
    env_path = BASE_DIR.parent / 'infra' / '.env'

load_dotenv(env_path)

# security WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-fallback-key')

# security WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# custom User Model
AUTH_USER_MODEL = 'accounts.User'

# frontend URL for emails
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

INSTALLED_APPS = [
    'daphne',  # Must be first for ASGI
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # For logout token blacklist
    'corsheaders',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    
    'api',
    'accounts.apps.AccountsConfig',           # Custom authentication
    'notifications',                          # Notifications system
    'repositories.apps.RepositoriesConfig',   # Repository management
    'scans.apps.ScansConfig',                 # Scanning system
    'monitoring',                             # System / worker monitoring
    'chat.apps.ChatConfig',                   # AI assistant chat
    'webhooks.apps.WebhooksConfig',           # GitHub webhook integration
    'audit.apps.AuditConfig',                 # Audit logging
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'secured_hub_db')),
        'USER': os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'secured_hub_user')),
        'PASSWORD': os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', '')),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# rest Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'EXCEPTION_HANDLER': 'api.utils.exception_handler.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672//')
# celery result backend is set below after Redis configuration
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 50

SPECTACULAR_SETTINGS = {
    'TITLE': 'SecuredHub API',
    'DESCRIPTION': 'Multi-tenant DevSecOps platform API documentation',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/v1',
    'SWAGGER_UI_DIST': 'SIDECAR',  # shorthand to use the sidecar instead
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
}

# jwt Configuration
SIMPLE_JWT = {
    # access token: 2 hours for better user experience in development
    # consider 30-60 minutes for production
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    
    # refresh token: 30 days for good user experience
    # users won't need to login frequently
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.getenv('JWT_SECRET_KEY', SECRET_KEY),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# cors Configuration
CORS_ALLOW_ALL_ORIGINS = False  # Set to False to use the whitelist below
CORS_ALLOWED_ORIGINS = [
    'https://sh-frontend.shabasdev.xyz',
    'https://securedhub.shabasdev.xyz',
    'http://localhost:3000',
    'http://localhost:5173',
    'http://localhost:5174',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:5174',
]

CSRF_TRUSTED_ORIGINS = [
    'https://sh-frontend.shabasdev.xyz',
    'https://securedhub.shabasdev.xyz',
    'https://sh-backend.shabasdev.xyz',
    'http://localhost:3000',
    'http://localhost:5173',
    'http://localhost:5174',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:5174',
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# logging Configuration
# email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# repository encryption Configuration
# for production, use a secure 32-byte key from environment variable
REPOSITORY_ENCRYPTION_KEY = os.getenv('REPOSITORY_ENCRYPTION_KEY', 'xmcC6B0bOp_Ldsurx5DAKQ6pGKcaPDfOMN6vE7qIbJc=')

# github OAuth Configuration
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', '')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', '')

# webhook Configuration
WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL', 'http://localhost:8001')

# redis cache / result backend configuration (supports Upstash via REDIS_URL)
REDIS_URL = os.getenv('REDIS_URL', '')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# detect if using Upstash (contains 'upstash' in hostname) - requires TLS
IS_UPSTASH = 'upstash' in REDIS_HOST.lower()

if REDIS_URL:
    redis_location = REDIS_URL
else:
    # use rediss:// (TLS) for Upstash, redis:// for local
    REDIS_SCHEME = 'rediss' if IS_UPSTASH else 'redis'
    REDIS_AUTH = f"default:{REDIS_PASSWORD}@" if REDIS_PASSWORD else ""
    redis_location = f"{REDIS_SCHEME}://{REDIS_AUTH}{REDIS_HOST}:{REDIS_PORT}/0"

redis_options = {
    "CLIENT_CLASS": "django_redis.client.DefaultClient",
}

# upstash and other managed providers commonly use rediss:// (TLS)
if redis_location.startswith("rediss://") or IS_UPSTASH:
    redis_options["CONNECTION_POOL_KWARGS"] = {"ssl_cert_reqs": None}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": redis_location,
        "OPTIONS": redis_options,
    }
}

# setting Celery result backend to use the same Redis location
# celery result backend (set after Redis config)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', redis_location)

# fix SSL for Celery if using rediss://
if CELERY_RESULT_BACKEND and CELERY_RESULT_BACKEND.startswith('rediss://'):
    if '?' not in CELERY_RESULT_BACKEND:
        CELERY_RESULT_BACKEND += '?ssl_cert_reqs=none'
    elif 'ssl_cert_reqs' not in CELERY_RESULT_BACKEND:
        CELERY_RESULT_BACKEND += '&ssl_cert_reqs=none'

# django channels configuration
ASGI_APPLICATION = 'core.asgi.application'

# building channel layer config based on Redis setup
if IS_UPSTASH or redis_location.startswith('rediss://'):
    # Upstash/TLS Redis - rediss:// URL handles SSL automatically
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [redis_location],
            },
        },
    }
elif REDIS_PASSWORD:
    # Authenticated Redis without TLS
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [redis_location],
            },
        },
    }
else:
    # local Redis without authentication
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [(
                    os.getenv('REDIS_HOST', 'redis'),
                    int(os.getenv('REDIS_PORT', 6379))
                )],
            },
        },
    }

# internal service URLs
# centralized configuration for all internal service endpoints
# change these in one place instead of hardcoding throughout the codebase

# rag (Retrieval-Augmented Generation) Service
RAG_SERVICE_URL = os.getenv('RAG_SERVICE_URL', 'http://rag-worker:8002')

# rabbitmq / message broker (already configured above in CELERY_BROKER_URL)

# redis (already configured above)

# adding other internal services here as needed
# sCANNER_WORKER_URL = os.getenv('SCANNER_WORKER_URL', 'http://scanner-worker:8003')

# internal Service Token
INTERNAL_SERVICE_TOKEN = os.getenv('INTERNAL_SERVICE_TOKEN', 'dev-internal-token')
