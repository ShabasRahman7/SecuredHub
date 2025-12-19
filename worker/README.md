# Worker Service - Standalone Celery Scanner

Independent Django microservice for processing security scans via Celery.

## Architecture

- **Independent Django Project**: Has its own `core/settings.py` and Django configuration
- **Shared Database**: Connects to the same PostgreSQL database as backend
- **RabbitMQ Communication**: Receives tasks from backend via RabbitMQ message queue
- **No Code Dependencies**: Does NOT import code from backend service

## Structure

```
worker/
├── core/                    # Django project (like backend/core/)
│   ├── settings.py          # Django settings
│   └── celery_app.py        # Celery configuration
├── scans/                   # Django app (like backend/scans/)
│   ├── models.py            # Scan models (managed=False)
│   ├── tasks.py             # Celery tasks
│   ├── services/            # Business logic services
│   │   └── github_security_api.py  # GitHub API client
│   └── utils.py             # Helper functions
├── manage.py                # Django manage.py
├── Dockerfile
├── requirements.txt
└── README.md
```

## Key Points

1. **Models are `managed=False`**: Worker models reference existing database tables created by backend migrations
2. **Communication via RabbitMQ**: Backend sends tasks using `send_task()`, worker processes them
3. **Shared Database**: Both services access the same PostgreSQL database
4. **Independent Deployment**: Worker can be deployed/updated independently

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DJANGO_SETTINGS_MODULE=core.settings
export DB_HOST=localhost
export DB_NAME=secured_hub_db
# ... other env vars

# Run Celery worker
celery -A core.celery_app worker --loglevel=info -Q celery,scans
```

## Docker

Built and run via `infra/docker-compose.yml` as `scanner-worker` service.

## Database Tables Used

- `scans_scan` - Scan records
- `scans_scanfinding` - Scan findings
- `repositories` - Repository information (read-only)
- `users` - User information (read-only)

All models are marked `managed=False` to prevent Django from creating migrations.
