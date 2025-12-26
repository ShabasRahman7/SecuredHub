"""
Enhanced Agent models with score prediction and file generation.

Request/response models for the production-grade AI Agent.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AgentGoal(str, Enum):
    """Types of goals the agent can accomplish."""
    ANALYZE_EVALUATION = "analyze_evaluation"
    COMPARE_REPOSITORIES = "compare_repositories"
    RECOMMEND_FIXES = "recommend_fixes"
    EXPLAIN_RULE = "explain_rule"
    GENERATE_FIX = "generate_fix"


class AgentRequest(BaseModel):
    """Request to run the AI agent."""
    
    goal: str = Field(
        description="Natural language goal for the agent, e.g. 'What should I fix first to pass SOC2?'"
    )
    evaluation_id: Optional[int] = Field(
        default=None,
        description="Evaluation ID if known"
    )
    repository_id: Optional[int] = Field(
        default=None, 
        description="Repository ID if known"
    )
    max_steps: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum reasoning steps"
    )


class ToolCall(BaseModel):
    """A single tool call made by the agent."""
    
    tool_name: str
    arguments: dict
    result: Optional[dict] = None


class ReasoningStep(BaseModel):
    """A single step in the agent's reasoning."""
    
    step_number: int
    thought: str = Field(description="Agent's reasoning")
    action: Optional[str] = Field(default=None, description="Tool called")
    observation: Optional[str] = Field(default=None, description="Tool result summary")


# Enhanced response models for score prediction

class FrameworkMapping(BaseModel):
    """Mapping to compliance frameworks."""
    soc2: list[str] = Field(default_factory=list)
    iso27001: list[str] = Field(default_factory=list)


class FixRecommendation(BaseModel):
    """A single fix recommendation with score impact."""
    
    rank: int = Field(description="Priority rank (1 = highest)")
    rule_name: str
    severity: str
    score_before: float = Field(description="Score before this fix")
    score_after: float = Field(description="Projected score after fix")
    impact_percent: float = Field(description="Score improvement in percentage points")
    framework_mapping: FrameworkMapping
    remediation_summary: str
    can_generate_fix: bool = Field(default=False)


class GeneratedFile(BaseModel):
    """A generated fix file."""
    
    filename: str = Field(description="Target path like '.github/CODEOWNERS'")
    content: str = Field(description="File content to commit")
    language: str = Field(default="text", description="For syntax highlighting")
    instructions: str = Field(description="How to apply this fix")


class AgentResponse(BaseModel):
    """Response from the AI agent."""
    
    # Goal and result
    goal: str
    result: str = Field(description="Final answer/analysis")
    
    # Score information (if evaluation analyzed)
    current_score: Optional[float] = Field(default=None)
    current_grade: Optional[str] = Field(default=None)
    projected_score: Optional[float] = Field(default=None, description="Score if all fixes applied")
    projected_grade: Optional[str] = Field(default=None)
    
    # Prioritized fixes with score impact
    prioritized_fixes: Optional[list[FixRecommendation]] = Field(default=None)
    
    # Generated files (if requested)
    generated_files: Optional[list[GeneratedFile]] = Field(default=None)
    
    # Framework summary
    framework_summary: Optional[dict] = Field(default=None)
    
    # Reasoning trace
    reasoning_steps: list[ReasoningStep]
    tool_calls: list[ToolCall]
    
    # Metadata
    steps_taken: int
    model_used: str
    success: bool
