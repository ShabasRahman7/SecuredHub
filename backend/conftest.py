"""
Shared pytest fixtures for SecuredHub backend tests.

This module provides reusable fixtures for:
- API client setup
- User and tenant creation
- Authentication helpers
"""
import pytest
from rest_framework.test import APIClient


# ============================================
# Database Fixtures
# ============================================

@pytest.fixture
def api_client():
    """Return an unauthenticated API test client."""
    return APIClient()


@pytest.fixture
def base_user(db):
    """Create a base user for tenant creation (no tenant membership yet)."""
    from accounts.models import User
    return User.objects.create_user(
        email="owner@test.com",
        password="testpass123",
        first_name="Test",
        last_name="Owner"
    )


@pytest.fixture
def tenant(db, base_user):
    """Create a test tenant/organization."""
    from accounts.models import Tenant
    return Tenant.objects.create(
        name="Test Organization",
        slug="test-org",
        created_by=base_user
    )


@pytest.fixture
def admin_user(db, tenant, base_user):
    """Create a tenant admin user (owner)."""
    from accounts.models import TenantMember
    # Create tenant membership for base user
    TenantMember.objects.create(
        user=base_user,
        tenant=tenant,
        role='owner'
    )
    return base_user


@pytest.fixture
def developer_user(db, tenant):
    """Create a developer user."""
    from accounts.models import User, TenantMember
    user = User.objects.create_user(
        email="dev@test.com",
        password="testpass123",
        first_name="Test",
        last_name="Developer",
        role="developer"
    )
    TenantMember.objects.create(
        user=user,
        tenant=tenant,
        role='member'
    )
    return user


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Return an API client authenticated as admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def developer_client(api_client, developer_user):
    """Return an API client authenticated as developer user."""
    api_client.force_authenticate(user=developer_user)
    return api_client


# ============================================
# Standards Fixtures
# ============================================

@pytest.fixture
def builtin_standard(db):
    """Create a built-in compliance standard."""
    from standards.models import ComplianceStandard
    return ComplianceStandard.objects.create(
        name="Test Standard",
        slug="test-standard",
        description="A test compliance standard",
        version="1.0",
        is_builtin=True,
        is_active=True
    )


@pytest.fixture
def compliance_rule(db, builtin_standard):
    """Create a compliance rule for the test standard."""
    from standards.models import ComplianceRule
    return ComplianceRule.objects.create(
        standard=builtin_standard,
        name="README Check",
        description="Checks for README.md file",
        rule_type="file_exists",
        check_config={"path": "README.md"},
        weight=5,
        severity="medium",
        is_active=True
    )


@pytest.fixture
def standard_with_rules(db, builtin_standard):
    """Create a standard with multiple rules."""
    from standards.models import ComplianceRule
    
    rules = [
        ComplianceRule(
            standard=builtin_standard,
            name="README Check",
            rule_type="file_exists",
            check_config={"path": "README.md"},
            weight=5,
            order=1
        ),
        ComplianceRule(
            standard=builtin_standard,
            name="LICENSE Check",
            rule_type="file_exists",
            check_config={"path": "LICENSE"},
            weight=3,
            order=2
        ),
        ComplianceRule(
            standard=builtin_standard,
            name="No .env File",
            rule_type="file_forbidden",
            check_config={"path": ".env"},
            weight=8,
            order=3
        ),
    ]
    ComplianceRule.objects.bulk_create(rules)
    return builtin_standard


# ============================================
# Repository Fixtures
# ============================================

@pytest.fixture
def repository(db, tenant):
    """Create a test repository."""
    from repositories.models import Repository
    return Repository.objects.create(
        tenant=tenant,
        name="test-repo",
        url="https://github.com/testorg/test-repo",
        default_branch="main",
        is_active=True
    )


@pytest.fixture
def repository_with_standard(db, repository, builtin_standard, admin_user):
    """Create a repository with an assigned standard."""
    from standards.models import RepositoryStandard
    RepositoryStandard.objects.create(
        repository=repository,
        standard=builtin_standard,
        assigned_by=admin_user,
        is_active=True
    )
    return repository


# ============================================
# Evaluation Fixtures
# ============================================

@pytest.fixture
def pending_evaluation(db, repository, builtin_standard, admin_user):
    """Create a pending evaluation."""
    from compliance.models import ComplianceEvaluation
    return ComplianceEvaluation.objects.create(
        repository=repository,
        standard=builtin_standard,
        triggered_by=admin_user,
        status='pending',
        commit_hash='abc123def456'
    )


@pytest.fixture
def completed_evaluation(db, repository, builtin_standard, admin_user):
    """Create a completed evaluation with score."""
    from compliance.models import ComplianceEvaluation, ComplianceScore
    from django.utils import timezone
    
    evaluation = ComplianceEvaluation.objects.create(
        repository=repository,
        standard=builtin_standard,
        triggered_by=admin_user,
        status='completed',
        commit_hash='abc123def456',
        started_at=timezone.now(),
        completed_at=timezone.now()
    )
    
    ComplianceScore.objects.create(
        evaluation=evaluation,
        total_score=85.0,
        passed_count=8,
        failed_count=2,
        total_rules=10,
        passed_weight=17,
        total_weight=20
    )
    
    return evaluation
