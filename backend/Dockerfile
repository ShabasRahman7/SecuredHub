# Use Python 3.10 slim image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# installing dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# installing test dependencies
RUN pip install --no-cache-dir \
    pytest==8.0.0 \
    pytest-django==4.7.0 \
    pytest-cov==4.1.0 \
    pytest-mock==3.12.0 \
    faker==22.0.0

# Copy project
COPY . /app/

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8001

# Run migrations and start server
CMD python manage.py migrate && python manage.py runserver 0.0.0.0:8001
