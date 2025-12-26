"""
Tests for Stage 2: AI Agent with tool calling.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.agent import AgentRequest, AgentResponse, ReasoningStep, ToolCall
from app.tools.base import ToolRegistry


class TestAgentEndpoint:
    """Tests for /api/v1/agent endpoint."""
    
    def test_agent_request_validation(self, client):
        """Invalid request should return 422."""
        response = client.post("/api/v1/agent", json={})
        assert response.status_code == 422
    
    def test_agent_valid_request(self, client):
        """Valid request structure should be accepted."""
        with patch("app.routers.agent.AgentService") as mock_agent:
            mock_service = MagicMock()
            mock_service.run = AsyncMock(return_value=AgentResponse(
                goal="Test goal",
                result="Test result",
                reasoning_steps=[],
                tool_calls=[],
                steps_taken=1,
                model_used="test-model",
                success=True,
            ))
            mock_agent.return_value = mock_service
            
            response = client.post(
                "/api/v1/agent",
                json={"goal": "Analyze evaluation 42"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["goal"] == "Test goal"
            assert data["success"] is True


class TestToolRegistry:
    """Tests for tool registry."""
    
    def test_tools_registered(self):
        """Verify tools are registered on import."""
        # Import to trigger registration
        import app.tools.evaluation_tools
        
        tools = ToolRegistry.list_tools()
        assert "get_evaluation" in tools
        assert "get_failures" in tools
        assert "get_repository" in tools
        assert "get_standard" in tools
        assert "get_score_history" in tools
    
    def test_get_function_declarations(self):
        """Function declarations should match expected format."""
        import app.tools.evaluation_tools
        
        declarations = ToolRegistry.get_function_declarations()
        assert len(declarations) >= 5
        
        # Check structure
        for decl in declarations:
            assert "name" in decl
            assert "description" in decl
            assert "parameters" in decl
    
    def test_unknown_tool_raises(self):
        """Executing unknown tool should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                ToolRegistry.execute("nonexistent_tool")
            )


class TestAgentModels:
    """Tests for agent models."""
    
    def test_agent_request_defaults(self):
        """AgentRequest should have sensible defaults."""
        request = AgentRequest(goal="Test")
        assert request.max_steps == 5
        assert request.evaluation_id is None
        assert request.repository_id is None
    
    def test_agent_response_structure(self):
        """AgentResponse should validate correctly."""
        response = AgentResponse(
            goal="Test",
            result="Result",
            reasoning_steps=[
                ReasoningStep(step_number=1, thought="Thinking")
            ],
            tool_calls=[
                ToolCall(tool_name="test", arguments={})
            ],
            steps_taken=1,
            model_used="test",
            success=True,
        )
        assert response.steps_taken == 1
        assert len(response.reasoning_steps) == 1
        assert len(response.tool_calls) == 1
