"""
Gemini AI Service for compliance analysis.

Uses the official google-genai SDK with structured output.
"""

import logging
from typing import Optional
from google import genai
from google.genai import types

from app.config import get_settings
from app.models.requests import EvaluationContext
from app.models.responses import (
    AnalyzeResponse,
    Recommendation,
    ScoreProjection,
    RemediationStep,
    FrameworkMapping,
    Priority,
)
from app.prompts.templates import SYSTEM_PROMPT, build_analysis_prompt

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Wrapper for Gemini API with structured output.
    
    Uses Pydantic models to ensure type-safe responses.
    """
    
    def __init__(self):
        """Initialize the Gemini client."""
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model
        logger.info(f"Initialized GeminiService with model: {self.model}")
    
    async def analyze_evaluation(
        self,
        context: EvaluationContext,
        max_recommendations: int = 5,
        include_remediation: bool = True,
        include_framework_mapping: bool = True,
    ) -> AnalyzeResponse:
        """
        Generate prioritized recommendations for an evaluation.
        
        Args:
            context: The evaluation context with failures
            max_recommendations: Maximum number of recommendations
            include_remediation: Whether to include remediation steps
            include_framework_mapping: Whether to include framework mappings
            
        Returns:
            AnalyzeResponse with prioritized recommendations
        """
        # Build the prompt
        prompt = build_analysis_prompt(
            repository_name=context.repository_name,
            standard_name=context.standard_name,
            current_score=context.score,
            grade=context.grade,
            total_rules=context.total_rules,
            passed_rules=context.passed_rules,
            failed_rules=context.failed_rules,
            failures=[f.model_dump() for f in context.failures],
            max_recommendations=max_recommendations,
            include_remediation=include_remediation,
            include_framework_mapping=include_framework_mapping,
        )
        
        logger.info(
            f"Analyzing evaluation {context.evaluation_id} for {context.repository_name}"
        )
        
        try:
            # Call Gemini with structured output using Pydantic schema
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.3,
                    top_p=0.95,
                    response_mime_type="application/json",
                    response_schema=AnalyzeResponse,
                ),
            )
            
            # Parse the response - google-genai handles JSON parsing
            if response.parsed:
                result = response.parsed
                logger.info(
                    f"Successfully analyzed evaluation {context.evaluation_id}, "
                    f"generated {len(result.recommendations)} recommendations"
                )
                return result
            
            # Fallback: try to parse text response
            if response.text:
                import json
                data = json.loads(response.text)
                result = AnalyzeResponse.model_validate(data)
                return result
            
            raise ValueError("Empty response from Gemini")
            
        except Exception as e:
            logger.error(f"Error analyzing evaluation: {e}")
            # Return a fallback response
            return self._create_fallback_response(context, str(e))
    
    def _create_fallback_response(
        self, 
        context: EvaluationContext, 
        error: str
    ) -> AnalyzeResponse:
        """Create a fallback response when AI fails."""
        
        # Generate basic recommendations from failures
        recommendations = []
        for i, failure in enumerate(context.failures[:5], 1):
            severity_to_priority = {
                "critical": Priority.CRITICAL,
                "high": Priority.HIGH,
                "medium": Priority.MEDIUM,
                "low": Priority.LOW,
            }
            
            weight_impact = (failure.weight / context.total_rules) * 100
            estimated_score = min(100, context.score + weight_impact)
            
            recommendations.append(
                Recommendation(
                    rule_id=failure.rule_id,
                    rule_name=failure.rule_name,
                    priority=severity_to_priority.get(failure.severity, Priority.MEDIUM),
                    priority_rank=i,
                    reason=f"Failed {failure.severity} severity rule with weight {failure.weight}",
                    business_impact=f"This rule affects compliance scoring",
                    current_score_impact=weight_impact,
                    estimated_score_after_fix=estimated_score,
                    remediation=[
                        RemediationStep(
                            step_number=1,
                            action="Review the failure",
                            details=failure.message
                        )
                    ],
                    framework_mappings=[],
                )
            )
        
        # Calculate projections
        total_possible_gain = sum(
            (f.weight / context.total_rules) * 100 
            for f in context.failures
        )
        
        return AnalyzeResponse(
            summary=f"Analysis generated with fallback due to AI error: {error}. "
                    f"Repository {context.repository_name} has {context.failed_rules} failing rules.",
            overall_assessment=f"Score: {context.score}% (Grade {context.grade}). "
                               f"Needs improvement on {context.failed_rules} rules.",
            recommendations=recommendations,
            score_projection=ScoreProjection(
                current_score=context.score,
                projected_score_all_fixed=min(100, context.score + total_possible_gain),
                quick_wins_score=min(100, context.score + total_possible_gain * 0.5),
                most_impactful_rules=[f.rule_name for f in context.failures[:3]],
            ),
            model_used=f"{self.model} (fallback)",
            confidence_score=0.3,
        )
    
    def close(self):
        """Close the Gemini client."""
        if hasattr(self.client, 'close'):
            self.client.close()


# Singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create the Gemini service singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


def close_gemini_service():
    """Close the Gemini service."""
    global _gemini_service
    if _gemini_service is not None:
        _gemini_service.close()
        _gemini_service = None
