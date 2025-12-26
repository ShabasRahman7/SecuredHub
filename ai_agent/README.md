# AI Compliance Agent

AI-powered compliance analysis service for SecurED-Hub.

## Features

- **Stage 1**: `/api/v1/analyze` - Structured recommendations from evaluation data
- **Stage 2**: `/api/v1/agent` - Agentic tool-calling for autonomous analysis

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export GEMINI_API_KEY=your_api_key

# Run development server
uvicorn app.main:app --reload --port 8002
```

## API Documentation

After starting the server, visit: `http://localhost:8002/docs`

## Architecture

```
app/
├── main.py          # FastAPI application
├── config.py        # Settings
├── routers/         # API endpoints
├── services/        # Business logic
├── models/          # Pydantic schemas
└── prompts/         # Prompt templates
```
