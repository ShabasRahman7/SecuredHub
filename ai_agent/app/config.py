"""
Configuration management using Pydantic Settings.

Loads configuration from environment variables with validation.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # LLM Provider - 'groq' (free) or 'gemini' (paid)
    llm_provider: str = "groq"
    
    # Groq API Configuration (FREE - https://console.groq.com)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Gemini API Configuration (optional - requires payment in some regions)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    
    # Service Configuration
    app_name: str = "SecuredHub AI Agent"
    debug: bool = False
    
    # Rate Limiting
    max_requests_per_minute: int = 30
    
    # Internal Service Communication
    django_api_url: str = "http://api:8001/api/v1"
    internal_service_token: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses LRU cache to avoid loading .env on every request.
    """
    return Settings()
