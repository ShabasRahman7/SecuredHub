"""
Evaluation tools for the AI Agent.

These tools allow the agent to fetch evaluation data from Django API.
"""

import httpx
import logging
from typing import Optional

from app.config import get_settings
from app.tools.base import tool, ToolResult

logger = logging.getLogger(__name__)


@tool(
    name="get_evaluation",
    description="Fetch details about a specific compliance evaluation including score, grade, and counts",
    parameters={
        "type": "object",
        "properties": {
            "evaluation_id": {
                "type": "integer",
                "description": "The ID of the evaluation to fetch",
            },
        },
        "required": ["evaluation_id"],
    },
)
async def get_evaluation(evaluation_id: int) -> dict:
    """
    Fetch evaluation details from Django API.
    
    Returns evaluation with score, grade, passed/failed counts.
    """
    settings = get_settings()
    url = f"{settings.django_api_url}/internal/compliance/evaluations/{evaluation_id}/"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {}
            if settings.internal_service_token:
                headers["X-Service-Token"] = settings.internal_service_token
            
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching evaluation {evaluation_id}: {e}")
        return {"success": False, "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching evaluation {evaluation_id}: {e}")
        return {"success": False, "error": str(e)}


@tool(
    name="get_failures",
    description="Fetch all failed rules for a specific evaluation with details and evidence",
    parameters={
        "type": "object",
        "properties": {
            "evaluation_id": {
                "type": "integer",
                "description": "The ID of the evaluation to get failures for",
            },
        },
        "required": ["evaluation_id"],
    },
)
async def get_failures(evaluation_id: int) -> dict:
    """
    Fetch failed rules for an evaluation.
    
    Returns list of failures with rule details and evidence.
    """
    settings = get_settings()
    url = f"{settings.django_api_url}/internal/compliance/evaluations/{evaluation_id}/failures/"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {}
            if settings.internal_service_token:
                headers["X-Service-Token"] = settings.internal_service_token
            
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching failures for {evaluation_id}: {e}")
        return {"success": False, "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching failures for {evaluation_id}: {e}")
        return {"success": False, "error": str(e)}


@tool(
    name="get_repository",
    description="Fetch repository information including name, URL, and default branch",
    parameters={
        "type": "object",
        "properties": {
            "repository_id": {
                "type": "integer",
                "description": "The ID of the repository to fetch",
            },
        },
        "required": ["repository_id"],
    },
)
async def get_repository(repository_id: int) -> dict:
    """
    Fetch repository details from Django API.
    """
    settings = get_settings()
    url = f"{settings.django_api_url}/internal/repositories/{repository_id}/"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {}
            if settings.internal_service_token:
                headers["X-Service-Token"] = settings.internal_service_token
            
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching repository {repository_id}: {e}")
        return {"success": False, "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching repository {repository_id}: {e}")
        return {"success": False, "error": str(e)}


@tool(
    name="get_standard",
    description="Fetch compliance standard details including name, description, and rule count",
    parameters={
        "type": "object",
        "properties": {
            "standard_id": {
                "type": "integer",
                "description": "The ID of the standard to fetch",
            },
        },
        "required": ["standard_id"],
    },
)
async def get_standard(standard_id: int) -> dict:
    """
    Fetch standard details from Django API.
    """
    settings = get_settings()
    url = f"{settings.django_api_url}/internal/standards/{standard_id}/"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {}
            if settings.internal_service_token:
                headers["X-Service-Token"] = settings.internal_service_token
            
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching standard {standard_id}: {e}")
        return {"success": False, "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching standard {standard_id}: {e}")
        return {"success": False, "error": str(e)}


@tool(
    name="get_score_history",
    description="Fetch historical compliance scores for a repository to show trends",
    parameters={
        "type": "object",
        "properties": {
            "repository_id": {
                "type": "integer",
                "description": "The ID of the repository",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of historical scores to fetch (default 10)",
            },
        },
        "required": ["repository_id"],
    },
)
async def get_score_history(repository_id: int, limit: int = 10) -> dict:
    """
    Fetch score history for a repository.
    
    Returns list of past scores for trend analysis.
    """
    settings = get_settings()
    url = f"{settings.django_api_url}/internal/repositories/{repository_id}/score-history/"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {}
            if settings.internal_service_token:
                headers["X-Service-Token"] = settings.internal_service_token
            
            response = await client.get(
                url, 
                headers=headers,
                params={"limit": limit}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching score history for {repository_id}: {e}")
        return {"success": False, "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching score history for {repository_id}: {e}")
        return {"success": False, "error": str(e)}
