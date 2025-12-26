"""
Test fixtures for AI Agent tests.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.requests import AnalyzeRequest, EvaluationContext, RuleFailure


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_failure():
    """Create a sample rule failure."""
    return RuleFailure(
        rule_id=1,
        rule_name="README.md exists",
        rule_type="file_exists",
        description="Repository must have a README.md file",
        severity="high",
        weight=10,
        message="README.md not found in repository root",
        evidence={"searched_path": "README.md"},
    )


@pytest.fixture
def sample_evaluation(sample_failure):
    """Create a sample evaluation context."""
    return EvaluationContext(
        repository_name="test-repo",
        repository_url="https://github.com/test/test-repo",
        default_branch="main",
        evaluation_id=42,
        score=65.0,
        grade="D",
        total_rules=10,
        passed_rules=6,
        failed_rules=4,
        standard_name="Startup Best Practices",
        standard_description="Essential engineering practices",
        failures=[
            sample_failure,
            RuleFailure(
                rule_id=2,
                rule_name="LICENSE file exists",
                rule_type="file_exists",
                description="Repository must have a LICENSE file",
                severity="medium",
                weight=8,
                message="LICENSE file not found",
                evidence={},
            ),
            RuleFailure(
                rule_id=3,
                rule_name="No .env committed",
                rule_type="file_forbidden",
                description="Environment files should not be committed",
                severity="critical",
                weight=10,
                message=".env file found in repository",
                evidence={"found_path": ".env"},
            ),
            RuleFailure(
                rule_id=4,
                rule_name=".gitignore exists",
                rule_type="file_exists",
                description="Repository must have a .gitignore file",
                severity="high",
                weight=9,
                message=".gitignore not found",
                evidence={},
            ),
        ],
    )


@pytest.fixture
def sample_request(sample_evaluation):
    """Create a sample analyze request."""
    return AnalyzeRequest(
        evaluation=sample_evaluation,
        include_remediation=True,
        include_framework_mapping=True,
        max_recommendations=5,
    )
