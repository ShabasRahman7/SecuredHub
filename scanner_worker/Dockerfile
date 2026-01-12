FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Gitleaks for secret scanning
RUN curl -sSL https://github.com/gitleaks/gitleaks/releases/download/v8.21.2/gitleaks_8.21.2_linux_x64.tar.gz \
    | tar -xz -C /usr/local/bin gitleaks \
    && chmod +x /usr/local/bin/gitleaks

# Install Trivy for dependency vulnerability scanning
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin v0.58.1

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Semgrep for multi-language SAST
RUN pip install --no-cache-dir semgrep

# Copy scanner worker code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

# Run Celery worker
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--concurrency=2"]
