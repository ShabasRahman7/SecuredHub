FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY app /app/app

ENV PYTHONPATH=/app:/app/backend
ENV PYTHONUNBUFFERED=1

CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info", "-Q", "celery,scans"]
