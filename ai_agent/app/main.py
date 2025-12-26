"""
FastAPI Application Entry Point.

SecurED-Hub AI Compliance Agent Service.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import analyze, agent
from app.services.gemini import get_gemini_service, close_gemini_service
from app.models.responses import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    
    Startup: Initialize LLM service (Groq or Gemini)
    Shutdown: Clean up resources
    """
    # Startup
    logger.info("Starting AI Agent service...")
    settings = get_settings()
    
    provider = settings.llm_provider
    logger.info(f"LLM Provider: {provider}")
    
    if provider == "groq":
        logger.info(f"Model: {settings.groq_model}")
        if not settings.groq_api_key:
            logger.error("GROQ_API_KEY not set! Get free key at https://console.groq.com")
        else:
            logger.info("Groq service ready")
    else:
        logger.info(f"Model: {settings.gemini_model}")
        try:
            get_gemini_service()
            logger.info("Gemini service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Agent service...")
    if provider != "groq":
        close_gemini_service()
    logger.info("AI Agent service closed")


# Create FastAPI application
app = FastAPI(
    title="SecurED-Hub AI Compliance Agent",
    description="""
    AI-powered compliance analysis and remediation recommendations.
    
    This service:
    - Analyzes compliance evaluation results
    - Prioritizes fixes by business impact
    - Maps failures to compliance frameworks (SOC2, ISO-27001)
    - Provides step-by-step remediation guidance
    - Predicts score improvements
    """,
    version="1.0.0",
    lifespan=lifespan,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler.
    
    Prevents raw exceptions from reaching client.
    """
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "detail": "An unexpected error occurred",
            "suggestion": "Please try again or contact support",
        },
    )


# Include Routers
app.include_router(analyze.router)
app.include_router(agent.router)


# Health Check Endpoint
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint for Docker/Kubernetes.
    
    Returns basic service status.
    """
    settings = get_settings()
    model = settings.groq_model if settings.llm_provider == "groq" else settings.gemini_model
    return HealthResponse(
        status="healthy",
        service="ai-agent",
        model=f"{settings.llm_provider}:{model}",
        version="1.0.0",
    )


# Root Endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint with service info."""
    return {
        "service": "SecurED-Hub AI Compliance Agent",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
