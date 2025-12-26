"""
Analysis endpoint for Stage 1.

POST /api/v1/analyze - Analyze evaluation and return recommendations.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.models.requests import AnalyzeRequest
from app.models.responses import AnalyzeResponse, ErrorResponse
from app.services.gemini import get_gemini_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Analyze compliance evaluation",
    description="""
    Analyze a compliance evaluation and return prioritized recommendations.
    
    The AI will:
    - Prioritize fixes by business impact
    - Map failures to compliance frameworks (SOC2, ISO-27001)
    - Provide step-by-step remediation guidance
    - Predict score improvements
    """,
)
async def analyze_evaluation(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze evaluation results and return recommendations.
    
    Args:
        request: AnalyzeRequest with evaluation context
        
    Returns:
        AnalyzeResponse with prioritized recommendations
    """
    evaluation = request.evaluation
    
    # Validate we have failures to analyze
    if not evaluation.failures:
        logger.info(
            f"Evaluation {evaluation.evaluation_id} has no failures, "
            "returning empty recommendations"
        )
        from app.models.responses import ScoreProjection
        from datetime import datetime
        
        return AnalyzeResponse(
            summary=f"Repository {evaluation.repository_name} passed all rules! "
                    f"Score: {evaluation.score}% (Grade {evaluation.grade}).",
            overall_assessment="Excellent compliance posture. No issues found.",
            recommendations=[],
            score_projection=ScoreProjection(
                current_score=evaluation.score,
                projected_score_all_fixed=evaluation.score,
                quick_wins_score=evaluation.score,
                most_impactful_rules=[],
            ),
            analysis_timestamp=datetime.utcnow().isoformat(),
            confidence_score=1.0,
        )
    
    try:
        logger.info(
            f"Analyzing evaluation {evaluation.evaluation_id} for "
            f"{evaluation.repository_name} ({evaluation.failed_rules} failures)"
        )
        
        gemini = get_gemini_service()
        result = await gemini.analyze_evaluation(
            context=evaluation,
            max_recommendations=request.max_recommendations,
            include_remediation=request.include_remediation,
            include_framework_mapping=request.include_framework_mapping,
        )
        
        return result
        
    except Exception as e:
        logger.exception(f"Error analyzing evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "analysis_failed",
                "detail": str(e),
                "suggestion": "Try again later or check AI service status",
            },
        )
