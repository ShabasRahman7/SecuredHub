"""Pydantic schemas for API requests/responses"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ChatInitRequest(BaseModel):
    """Request to initialize chat for a finding"""
    finding_id: int = Field(..., description="ID of the scan finding")
    finding: Dict = Field(..., description="Full finding details")

class ChatInitResponse(BaseModel):
    """Response from chat initialization"""
    message: str = Field(..., description="Initial AI message")
    finding_id: int

class ChatRequest(BaseModel):
    """Request to send a message in chat"""
    finding_id: int
    message: str = Field(..., min_length=1, description="User's message")
    conversation_history: List[Dict] = Field(default_factory=list, description="Previous messages")
    finding: Optional[Dict] = Field(default=None, description="Finding details with context")

class ChatResponse(BaseModel):
    """Response from chat"""
    reply: str = Field(..., description="AI's response")
    finding_id: int

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    knowledge_base_count: int
    embedding_model: str
    llm_model: str
