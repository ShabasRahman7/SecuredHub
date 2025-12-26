# Worker Service - Compliance Evaluator

Independent Celery worker for processing compliance evaluations.

## Architecture

- **Standalone Django Project**: Own `core/settings.py` and Celery configuration
- **Shared Database**: Connects to PostgreSQL alongside backend
- **RabbitMQ Queue**: Receives evaluation tasks from backend
- **No Code Dependencies**: Does not import from backend service

## Structure

```
worker/
├── core/                    # Django project settings
│   ├── settings.py
│   └── celery_app.py
├── compliance/              # Compliance evaluation engine
│   ├── evaluator.py         # Main orchestrator
│   ├── collectors/          # GitHub data fetchers
│   └── rules/               # Rule implementations
│       ├── base.py          # BaseRule, RuleRegistry
│       ├── file_rules.py    # FileExists, FileForbidden
│       ├── folder_rules.py  # FolderExists
│       ├── config_rules.py  # ConfigCheck (JSON)
│       ├── hygiene_rules.py # Gitignore, CI, CODEOWNERS
│       └── pattern_rules.py # PatternMatch (glob)
├── compliance_models/       # Read-only Django models
├── conftest.py              # Test fixtures
└── requirements.txt
```

## Running Locally

```bash
pip install -r requirements.txt

export DJANGO_SETTINGS_MODULE=core.settings
export DB_HOST=localhost
# ... other env vars

celery -A core.celery_app worker --loglevel=info -Q celery,compliance
```

## Docker

Run via `infra/docker-compose.yml` as `compliance-worker` service.

## Testing

```bash
pytest -v  # 102 tests
```
