"""
Agent endpoint for Stage 2.

POST /api/v1/agent - Run AI agent with tool calling.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.models.agent import AgentRequest, AgentResponse
from app.models.responses import ErrorResponse
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Agent"])


@router.post(
    "/agent",
    response_model=AgentResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Run AI agent with tool calling",
    description="""
    Run the AI compliance agent with autonomous tool calling.
    
    The agent will:
    - Interpret your goal
    - Decide which tools to call (get_evaluation, get_failures, etc.)
    - Execute multi-step reasoning (ReAct pattern)
    - Synthesize a final response
    
    This is a true AI agent that autonomously decides its actions.
    """,
)
async def run_agent(request: AgentRequest) -> AgentResponse:
    """
    Run the AI agent with the given goal.
    
    The agent uses ReAct (Reason + Act) pattern:
    1. Think about what to do
    2. Call a tool
    3. Observe the result
    4. Repeat until done
    """
    logger.info(f"Running agent with goal: {request.goal}")
    
    try:
        agent = AgentService()
        result = await agent.run(
            goal=request.goal,
            evaluation_id=request.evaluation_id,
            repository_id=request.repository_id,
            max_steps=request.max_steps,
        )
        return result
        
    except Exception as e:
        logger.exception(f"Agent error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "agent_failed",
                "detail": str(e),
                "suggestion": "Try again with a simpler goal",
            },
        )
