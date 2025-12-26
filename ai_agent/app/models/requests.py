"""
Request models for the AI Agent API.

These define the structure of data we expect from Django.
Pydantic validates this automatically.
"""

from pydantic import BaseModel, Field
from typing import Optional


class RuleFailure(BaseModel):
    """A single rule that failed during evaluation."""
    
    rule_id: int = Field(description="Database ID of the rule")
    rule_name: str = Field(description="Human-readable rule name")
    rule_type: str = Field(description="Type: file_exists, config_check, etc.")
    description: str = Field(default="", description="What this rule checks")
    severity: str = Field(description="critical, high, medium, low")
    weight: int = Field(ge=1, le=10, description="Rule weight 1-10")
    message: str = Field(description="Why it failed")
    evidence: dict = Field(default_factory=dict, description="Failure details")


class EvaluationContext(BaseModel):
    """Complete context for AI analysis."""
    
    # Repository Information
    repository_name: str
    repository_url: str
    default_branch: str = "main"
    
    # Evaluation Results
    evaluation_id: int
    score: float = Field(ge=0, le=100)
    grade: str = Field(pattern="^[A-F]$")
    total_rules: int
    passed_rules: int
    failed_rules: int
    
    # Standard Information
    standard_name: str
    standard_description: str = ""
    
    # The Failed Rules (this is what AI analyzes)
    failures: list[RuleFailure]
    
    # Optional Context
    organization_name: Optional[str] = None
    previous_score: Optional[float] = None


class AnalyzeRequest(BaseModel):
    """
    Request to analyze an evaluation.
    
    Contains evaluation data and analysis options.
    """
    
    evaluation: EvaluationContext
    
    # Analysis Options
    include_remediation: bool = True
    include_framework_mapping: bool = True
    max_recommendations: int = Field(default=5, ge=1, le=10)
