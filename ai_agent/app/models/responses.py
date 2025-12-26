"""
Response models for the AI Agent API.

These define the structure of our recommendations.
The AI response is validated against these models.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class Priority(str, Enum):
    """Fix priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FrameworkMapping(BaseModel):
    """Maps a rule failure to compliance frameworks."""
    
    framework: str = Field(description="e.g., SOC2, ISO-27001")
    control: str = Field(description="e.g., CC6.1, A.12.6.1")
    requirement: str = Field(description="Human-readable requirement")


class RemediationStep(BaseModel):
    """A single step to fix an issue."""
    
    step_number: int
    action: str = Field(description="What to do")
    details: Optional[str] = Field(default=None, description="How to do it")


class Recommendation(BaseModel):
    """
    A single prioritized recommendation.
    
    This is the core output - what the developer sees.
    """
    
    # Which rule this addresses
    rule_id: int
    rule_name: str
    
    # Prioritization
    priority: Priority
    priority_rank: int = Field(ge=1, description="1 = fix first")
    
    # Why it matters
    reason: str = Field(description="Why fix this first")
    business_impact: str = Field(description="Business consequence of not fixing")
    
    # Score impact
    current_score_impact: float = Field(description="How much this rule affects score")
    estimated_score_after_fix: float = Field(
        ge=0, le=100,
        description="Predicted score after fixing this"
    )
    
    # How to fix
    remediation: list[RemediationStep] = Field(default_factory=list)
    
    # Compliance context
    framework_mappings: list[FrameworkMapping] = Field(default_factory=list)


class ScoreProjection(BaseModel):
    """Score improvement projections."""
    
    current_score: float
    projected_score_all_fixed: float
    quick_wins_score: float = Field(description="Score if top 3 issues fixed")
    most_impactful_rules: list[str] = Field(description="Rules with biggest impact")


class AnalyzeResponse(BaseModel):
    """
    Complete AI analysis response.
    
    This is what Django receives and passes to the frontend.
    """
    
    # Summary
    summary: str = Field(description="One-paragraph executive summary")
    overall_assessment: str = Field(description="Overall compliance posture")
    
    # Recommendations (sorted by priority)
    recommendations: list[Recommendation]
    
    # Score Predictions
    score_projection: ScoreProjection
    
    # Metadata
    analysis_timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    model_used: str = "gemini-2.0-flash"
    confidence_score: float = Field(ge=0, le=1, description="AI confidence 0-1")


class ErrorResponse(BaseModel):
    """Error response structure."""
    
    error: str
    detail: str
    suggestion: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = "healthy"
    service: str = "ai-agent"
    model: str
    version: str = "1.0.0"
