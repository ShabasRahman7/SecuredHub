"""
Groq LLM Service - Free alternative to Gemini.

Groq offers completely free API access with generous limits:
- 30 requests per minute
- Multiple free models (llama3, mixtral)

To get API key: https://console.groq.com (free, no payment)
"""

import logging
from typing import Optional
from groq import Groq

from app.config import get_settings
from app.models.requests import AnalyzeRequest
from app.models.responses import AnalyzeResponse, Recommendation, ScoreProjection, Priority

logger = logging.getLogger(__name__)


class GroqService:
    """
    Groq-based LLM service.
    
    Uses Groq's free API for compliance analysis.
    """
    
    _instance: Optional["GroqService"] = None
    
    def __init__(self):
        settings = get_settings()
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model or "llama-3.3-70b-versatile"
        logger.info(f"Initialized GroqService with model: {self.model}")
    
    @classmethod
    def get_instance(cls) -> "GroqService":
        if cls._instance is None:
            cls._instance = GroqService()
        return cls._instance
    
    async def analyze_evaluation(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """Analyze evaluation and return recommendations."""
        
        evaluation = request.evaluation
        
        # Build prompt
        prompt = self._build_prompt(evaluation)
        
        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an AI Compliance Agent for SecurED-Hub.
Analyze the evaluation results and provide:
1. A brief summary of the compliance status
2. Prioritized recommendations for fixing issues
3. Score projection if issues are fixed

Format your response as JSON with this structure:
{
    "summary": "Brief summary of compliance status",
    "recommendations": [
        {
            "priority_rank": 1,
            "priority": "critical|high|medium|low",
            "rule_name": "Rule name",
            "reason": "Why this is important",
            "business_impact": "Business impact",
            "current_score_impact": 5.0,
            "remediation": [{"step_number": 1, "action": "What to do", "details": "Details"}]
        }
    ],
    "score_projection": {
        "current_score": 65.0,
        "projected_score_all_fixed": 95.0
    },
    "confidence_score": 0.85
}"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Try to parse JSON from response
            import json
            try:
                # Find JSON in response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    data = json.loads(content[start:end])
                    return self._parse_response(data, evaluation)
            except json.JSONDecodeError:
                pass
            
            # Fallback - return as summary
            return self._create_fallback_response(content, evaluation)
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    def _build_prompt(self, evaluation) -> str:
        """Build analysis prompt."""
        failures_text = ""
        for i, f in enumerate(evaluation.failures[:10], 1):
            failures_text += f"\n{i}. {f.rule_name} (severity: {f.severity}, weight: {f.weight})"
            failures_text += f"\n   - {f.description or 'No description'}"
            if f.message:
                failures_text += f"\n   - Message: {f.message}"
        
        return f"""Analyze this compliance evaluation:

Repository: {evaluation.repository_name}
Standard: {evaluation.standard_name}
Current Score: {evaluation.score}% (Grade: {evaluation.grade})
Rules: {evaluation.passed_rules} passed, {evaluation.failed_rules} failed

Failed Rules:{failures_text}

Provide prioritized recommendations to improve compliance score."""
    
    def _parse_response(self, data: dict, evaluation) -> AnalyzeResponse:
        """Parse JSON response into AnalyzeResponse."""
        recommendations = []
        for rec in data.get("recommendations", [])[:5]:
            priority = rec.get("priority", "medium")
            if priority not in ["critical", "high", "medium", "low"]:
                priority = "medium"
            
            recommendations.append(Recommendation(
                priority_rank=rec.get("priority_rank", 1),
                priority=Priority(priority),
                rule_name=rec.get("rule_name", "Unknown"),
                reason=rec.get("reason", ""),
                business_impact=rec.get("business_impact", ""),
                current_score_impact=float(rec.get("current_score_impact", 0)),
                estimated_score_after_fix=evaluation.score + float(rec.get("current_score_impact", 0)),
                remediation=[],
                framework_mappings=[],
            ))
        
        score_proj = data.get("score_projection", {})
        
        return AnalyzeResponse(
            summary=data.get("summary", "Analysis complete."),
            recommendations=recommendations,
            score_projection=ScoreProjection(
                current_score=evaluation.score,
                projected_score_all_fixed=score_proj.get("projected_score_all_fixed", 100.0),
                rules_to_fix=evaluation.failed_rules,
            ),
            confidence_score=data.get("confidence_score", 0.8),
        )
    
    def _create_fallback_response(self, content: str, evaluation) -> AnalyzeResponse:
        """Create fallback response when JSON parsing fails."""
        return AnalyzeResponse(
            summary=content[:500] if content else "Analysis complete.",
            recommendations=[],
            score_projection=ScoreProjection(
                current_score=evaluation.score,
                projected_score_all_fixed=100.0,
                rules_to_fix=evaluation.failed_rules,
            ),
            confidence_score=0.6,
        )


# Singleton access
_groq_service: Optional[GroqService] = None


def get_groq_service() -> GroqService:
    global _groq_service
    if _groq_service is None:
        _groq_service = GroqService()
    return _groq_service


def close_groq_service():
    global _groq_service
    _groq_service = None
