"""Unit tests for repositories app models."""
import pytest
from repositories.models import Repository, TenantCredential, RepositoryAssignment
from accounts.models import User, TenantMember


@pytest.mark.django_db
class TestRepository:
    """Tests for the Repository model."""
    
    def test_create_repository(self, tenant):
        """Test creating a repository."""
        repo = Repository.objects.create(
            tenant=tenant,
            name='test-repo',
            url='https://github.com/test/repo',
            default_branch='main'
        )
        
        assert repo.id is not None
        assert repo.name == 'test-repo'
        assert repo.is_active is True
    
    def test_repository_str(self, tenant):
        """Test __str__ method."""
        repo = Repository.objects.create(
            tenant=tenant,
            name='my-app',
            url='https://github.com/test/my-app'
        )
        
        s = str(repo)
        assert 'my-app' in s
        assert tenant.name in s
    
    def test_repository_default_branch(self, tenant):
        """Test default branch defaults to 'main'."""
        repo = Repository.objects.create(
            tenant=tenant,
            name='test-repo',
            url='https://github.com/test/repo'
        )
        
        assert repo.default_branch == 'main'
    
    def test_unique_together_tenant_url(self, tenant):
        """Test unique constraint on tenant + url."""
        Repository.objects.create(
            tenant=tenant,
            name='repo1',
            url='https://github.com/test/unique'
        )
        
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Repository.objects.create(
                tenant=tenant,
                name='repo2',
                url='https://github.com/test/unique'  # Same URL
            )



@pytest.mark.django_db
class TestTenantCredential:
    """Tests for the TenantCredential model."""
    
    def test_create_credential(self, tenant):
        """Test creating a credential."""
        cred = TenantCredential.objects.create(
            tenant=tenant,
            name='GitHub Token',
            provider='github',
            encrypted_access_token=''
        )
        
        assert cred.id is not None
        assert cred.provider == 'github'
        assert cred.is_active is True
    
    def test_credential_str(self, tenant):
        """Test __str__ method."""
        cred = TenantCredential.objects.create(
            tenant=tenant,
            name='My GitHub',
            provider='github',
            encrypted_access_token=''
        )
        
        s = str(cred)
        assert 'My GitHub' in s
        assert 'github' in s.lower()
    
    def test_has_access_token_empty(self, tenant):
        """Test has_access_token returns False when empty."""
        cred = TenantCredential.objects.create(
            tenant=tenant,
            name='Empty Token',
            provider='github',
            encrypted_access_token=''
        )
        
        assert cred.has_access_token is False
    
    def test_has_access_token_set(self, tenant):
        """Test has_access_token returns True when set."""
        cred = TenantCredential.objects.create(
            tenant=tenant,
            name='Has Token',
            provider='github',
            encrypted_access_token='encrypted_data_here'
        )
        
        assert cred.has_access_token is True
    
    def test_repositories_count(self, tenant):
        """Test repositories_count property."""
        cred = TenantCredential.objects.create(
            tenant=tenant,
            name='Multi Repo Cred',
            provider='github',
            encrypted_access_token=''
        )
        
        # Create repos with this credential
        Repository.objects.create(
            tenant=tenant,
            name='repo1',
            url='https://github.com/test/repo1',
            credential=cred
        )
        Repository.objects.create(
            tenant=tenant,
            name='repo2',
            url='https://github.com/test/repo2',
            credential=cred
        )
        
        assert cred.repositories_count == 2
    
    def test_unique_together_tenant_name(self, tenant):
        """Test unique constraint on tenant + name."""
        TenantCredential.objects.create(
            tenant=tenant,
            name='Unique Cred',
            provider='github',
            encrypted_access_token=''
        )
        
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            TenantCredential.objects.create(
                tenant=tenant,
                name='Unique Cred',  # Same name
                provider='gitlab',
                encrypted_access_token=''
            )



@pytest.mark.django_db
class TestRepositoryAssignment:
    """Tests for the RepositoryAssignment model."""
    
    def test_create_assignment(self, repository, tenant):
        """Test creating an assignment."""
        user = User.objects.create_user(email='assigned_dev@test.com', password='pass')
        member = TenantMember.objects.create(
            user=user,
            tenant=tenant,
            role='member'
        )
        
        assignment = RepositoryAssignment.objects.create(
            repository=repository,
            member=member,
            assigned_by=user
        )
        
        assert assignment.id is not None
        assert assignment.assigned_at is not None
    
    def test_assignment_str(self, repository, tenant):
        """Test __str__ method."""
        user = User.objects.create_user(email='assignee@test.com', password='pass')
        member = TenantMember.objects.create(
            user=user,
            tenant=tenant,
            role='member'
        )
        
        assignment = RepositoryAssignment.objects.create(
            repository=repository,
            member=member
        )
        
        s = str(assignment)
        assert 'assignee@test.com' in s
        assert repository.name in s
    
    def test_unique_together_repo_member(self, repository, tenant):
        """Test unique constraint on repository + member."""
        user = User.objects.create_user(email='double@test.com', password='pass')
        member = TenantMember.objects.create(
            user=user,
            tenant=tenant,
            role='member'
        )
        
        RepositoryAssignment.objects.create(
            repository=repository,
            member=member
        )
        
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            RepositoryAssignment.objects.create(
                repository=repository,
                member=member  # Same assignment
            )
