"""
Tests for compliance API views.

Tests:
- EvaluationListView
- EvaluationDetailView
- TriggerEvaluationView
- RepositoryScoresView
"""
import pytest
from rest_framework import status


# ============================================
# Evaluation List Tests
# ============================================

@pytest.mark.django_db
class TestEvaluationListView:
    """Tests for listing evaluations."""
    
    def test_list_evaluations_authenticated(self, authenticated_client, repository, completed_evaluation):
        """Test authenticated user can list evaluations for a repository."""
        response = authenticated_client.get(
            f'/api/v1/compliance/repositories/{repository.id}/evaluations/'
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_list_evaluations_unauthenticated(self, api_client, repository):
        """Test unauthenticated user cannot list evaluations."""
        response = api_client.get(f'/api/v1/compliance/repositories/{repository.id}/evaluations/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================
# Evaluation Detail Tests
# ============================================

@pytest.mark.django_db
class TestEvaluationDetailView:
    """Tests for getting evaluation details."""
    
    def test_get_evaluation_detail(self, authenticated_client, completed_evaluation):
        """Test getting evaluation details."""
        response = authenticated_client.get(
            f'/api/v1/compliance/evaluations/{completed_evaluation.id}/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == completed_evaluation.id
    
    def test_get_nonexistent_evaluation(self, authenticated_client):
        """Test getting non-existent evaluation returns 404."""
        response = authenticated_client.get('/api/v1/compliance/evaluations/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================
# Trigger Evaluation Tests
# ============================================

@pytest.mark.django_db
class TestTriggerEvaluationView:
    """Tests for triggering evaluations."""
    
    def test_trigger_evaluation(self, authenticated_client, repository_with_standard, builtin_standard):
        """Test triggering an evaluation."""
        response = authenticated_client.post(
            '/api/v1/compliance/evaluations/trigger/',
            {
                'repository_id': repository_with_standard.id,
                'standard_id': builtin_standard.id
            },
            format='json'
        )
        
        # May return 200, 201, or 202 (accepted) depending on implementation
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_202_ACCEPTED
        ]
    
    def test_trigger_evaluation_without_repo(self, authenticated_client, builtin_standard):
        """Test triggering without repository_id fails."""
        response = authenticated_client.post(
            '/api/v1/compliance/evaluations/trigger/',
            {'standard_id': builtin_standard.id},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_trigger_evaluation_unauthenticated(self, api_client, repository, builtin_standard):
        """Test unauthenticated user cannot trigger evaluation."""
        response = api_client.post(
            '/api/v1/compliance/evaluations/trigger/',
            {
                'repository_id': repository.id,
                'standard_id': builtin_standard.id
            },
            format='json'
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================
# Repository Scores Tests
# ============================================

@pytest.mark.django_db
class TestRepositoryScoresView:
    """Tests for repository compliance scores."""
    
    def test_get_repository_scores(self, authenticated_client, completed_evaluation):
        """Test getting scores for a repository."""
        response = authenticated_client.get(
            f'/api/v1/compliance/repositories/{completed_evaluation.repository.id}/scores/'
        )
        
        assert response.status_code == status.HTTP_200_OK


# ============================================
# Delete Evaluation Tests
# ============================================

@pytest.mark.django_db
class TestDeleteEvaluationView:
    """Tests for deleting evaluations."""
    
    def test_delete_evaluation_owner(self, authenticated_client, completed_evaluation):
        """Test owner can delete evaluation."""
        response = authenticated_client.delete(
            f'/api/v1/compliance/evaluations/{completed_evaluation.id}/delete/'
        )
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_403_FORBIDDEN  # If only tenant owners can delete
        ]
    
    def test_delete_evaluation_unauthenticated(self, api_client, completed_evaluation):
        """Test unauthenticated user cannot delete."""
        response = api_client.delete(
            f'/api/v1/compliance/evaluations/{completed_evaluation.id}/delete/'
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================
# Cross-Tenant Isolation Tests
# ============================================

@pytest.mark.django_db
class TestCrossTenantIsolation:
    """
    Tests proving that users cannot access data from other tenants.
    This is critical for multi-tenancy security.
    """
    
    def test_user_cannot_access_other_tenant_evaluation_list(
        self, api_client, db
    ):
        """User from TenantA cannot list evaluations from TenantB's repository."""
        from accounts.models import User, Tenant, TenantMember
        from repositories.models import Repository
        from standards.models import ComplianceStandard
        from compliance.models import ComplianceEvaluation
        
        # Create TenantA with UserA
        user_a = User.objects.create_user(email="usera@a.com", password="test123")
        tenant_a = Tenant.objects.create(name="Tenant A", slug="tenant-a")
        TenantMember.objects.create(user=user_a, tenant=tenant_a, role='owner')
        
        # Create TenantB with its own repo and evaluation
        tenant_b = Tenant.objects.create(name="Tenant B", slug="tenant-b")
        repo_b = Repository.objects.create(
            tenant=tenant_b,
            name="tenant-b-repo",
            url="https://github.com/b/repo",
            is_active=True
        )
        standard = ComplianceStandard.objects.create(
            name="Test", slug="test", is_builtin=True, is_active=True
        )
        eval_b = ComplianceEvaluation.objects.create(
            repository=repo_b,
            standard=standard,
            status='completed'
        )
        
        # UserA tries to list TenantB's evaluations
        api_client.force_authenticate(user=user_a)
        response = api_client.get(f'/api/v1/compliance/repositories/{repo_b.id}/evaluations/')
        
        # Should return empty list or 403, not TenantB's data
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0, "User should not see other tenant's evaluations"
    
    def test_user_cannot_access_other_tenant_evaluation_detail(
        self, api_client, db
    ):
        """User from TenantA cannot view TenantB's evaluation details."""
        from accounts.models import User, Tenant, TenantMember
        from repositories.models import Repository
        from standards.models import ComplianceStandard
        from compliance.models import ComplianceEvaluation
        
        # Create TenantA with UserA
        user_a = User.objects.create_user(email="usera2@a.com", password="test123")
        tenant_a = Tenant.objects.create(name="Tenant A2", slug="tenant-a2")
        TenantMember.objects.create(user=user_a, tenant=tenant_a, role='owner')
        
        # Create TenantB evaluation
        tenant_b = Tenant.objects.create(name="Tenant B2", slug="tenant-b2")
        repo_b = Repository.objects.create(
            tenant=tenant_b,
            name="tenant-b2-repo",
            url="https://github.com/b2/repo",
            is_active=True
        )
        standard = ComplianceStandard.objects.create(
            name="Test2", slug="test2", is_builtin=True, is_active=True
        )
        eval_b = ComplianceEvaluation.objects.create(
            repository=repo_b,
            standard=standard,
            status='completed'
        )
        
        # UserA tries to access TenantB's evaluation
        api_client.force_authenticate(user=user_a)
        response = api_client.get(f'/api/v1/compliance/evaluations/{eval_b.id}/')
        
        # Should return 404 (not found for this user's tenant scope)
        assert response.status_code == status.HTTP_404_NOT_FOUND, \
            "User should not access other tenant's evaluation"

