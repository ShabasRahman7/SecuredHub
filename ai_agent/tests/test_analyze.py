"""
Tests for /api/v1/analyze endpoint.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.responses import (
    AnalyzeResponse,
    Recommendation,
    ScoreProjection,
    RemediationStep,
    Priority,
)


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Health check should return 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-agent"
    
    def test_root_endpoint(self, client):
        """Root endpoint should return service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data


class TestAnalyzeEndpoint:
    """Tests for /api/v1/analyze endpoint."""
    
    def test_analyze_request_validation(self, client):
        """Invalid request should return 422."""
        response = client.post("/api/v1/analyze", json={})
        assert response.status_code == 422
    
    def test_analyze_empty_failures(self, client, sample_evaluation):
        """Evaluation with no failures should return empty recommendations."""
        sample_evaluation.failures = []
        sample_evaluation.failed_rules = 0
        sample_evaluation.passed_rules = 10
        sample_evaluation.score = 100.0
        sample_evaluation.grade = "A"
        
        response = client.post(
            "/api/v1/analyze",
            json={
                "evaluation": sample_evaluation.model_dump(),
                "include_remediation": True,
                "include_framework_mapping": True,
                "max_recommendations": 5,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) == 0
        assert data["confidence_score"] == 1.0
    
    @patch("app.routers.analyze.get_gemini_service")
    def test_analyze_success(self, mock_gemini, client, sample_request):
        """Successful analysis should return recommendations."""
        # Create mock response
        mock_response = AnalyzeResponse(
            summary="Test summary",
            overall_assessment="Test assessment",
            recommendations=[
                Recommendation(
                    rule_id=1,
                    rule_name="README.md exists",
                    priority=Priority.HIGH,
                    priority_rank=1,
                    reason="High impact rule",
                    business_impact="Documentation is critical",
                    current_score_impact=10.0,
                    estimated_score_after_fix=75.0,
                    remediation=[
                        RemediationStep(
                            step_number=1,
                            action="Create README.md",
                            details="Add project description",
                        )
                    ],
                    framework_mappings=[],
                )
            ],
            score_projection=ScoreProjection(
                current_score=65.0,
                projected_score_all_fixed=100.0,
                quick_wins_score=85.0,
                most_impactful_rules=["README.md exists"],
            ),
            confidence_score=0.9,
        )
        
        # Setup mock - use AsyncMock for async method
        mock_service = MagicMock()
        mock_service.analyze_evaluation = AsyncMock(return_value=mock_response)
        mock_gemini.return_value = mock_service
        
        response = client.post(
            "/api/v1/analyze",
            json=sample_request.model_dump(),
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0
    
    @patch("app.routers.analyze.get_gemini_service")
    def test_analyze_error_handling(self, mock_gemini, client, sample_request):
        """AI error should return 500 with details."""
        mock_service = MagicMock()
        mock_service.analyze_evaluation = AsyncMock(side_effect=Exception("AI service error"))
        mock_gemini.return_value = mock_service
        
        response = client.post(
            "/api/v1/analyze",
            json=sample_request.model_dump(),
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


class TestPydanticModels:
    """Tests for Pydantic model validation."""
    
    def test_rule_failure_validation(self, sample_failure):
        """RuleFailure should validate correctly."""
        assert sample_failure.rule_id == 1
        assert sample_failure.severity == "high"
        assert sample_failure.weight == 10
    
    def test_evaluation_context_validation(self, sample_evaluation):
        """EvaluationContext should validate correctly."""
        assert sample_evaluation.score >= 0
        assert sample_evaluation.score <= 100
        assert sample_evaluation.grade in "ABCDF"
    
    def test_recommendation_validation(self):
        """Recommendation should validate correctly."""
        rec = Recommendation(
            rule_id=1,
            rule_name="Test",
            priority=Priority.HIGH,
            priority_rank=1,
            reason="Test reason",
            business_impact="Test impact",
            current_score_impact=5.0,
            estimated_score_after_fix=70.0,
        )
        assert rec.priority == Priority.HIGH
        assert rec.priority_rank == 1
