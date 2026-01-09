# unit tests for repositories app models
import pytest
from django.db import IntegrityError
from repositories.models import TenantCredential, Repository, RepositoryAssignment


@pytest.mark.django_db
class TestTenantCredentialModel:
    # testing TenantCredential model with encryption
    
    def test_credential_creation_success(self, db, test_tenant, test_user):
        # should create credential successfully
        credential = TenantCredential.objects.create(
            tenant=test_tenant,
            name="GitHub Main",
            provider=TenantCredential.PROVIDER_GITHUB,
            github_account_login="testuser",
            added_by=test_user
        )
        assert credential.name == "GitHub Main"
        assert credential.provider == TenantCredential.PROVIDER_GITHUB
    
    def test_set_access_token_encrypts(self, test_credential):
        # should encrypt access token when stored
        plain_token = "github_pat_12345_secret"
        test_credential.set_access_token(plain_token)
        test_credential.save()
        
        # encrypted value should not equal plain text
        assert test_credential.encrypted_access_token != plain_token
        # should be base64 encoded
        assert test_credential.encrypted_access_token != ''
    
    def test_get_access_token_decrypts(self, test_credential):
        # should decrypt access token when retrieved
        plain_token = "github_pat_secret_67890"
        test_credential.set_access_token(plain_token)
        test_credential.save()
        
        decrypted = test_credential.get_access_token()
        assert decrypted == plain_token
    
    def test_has_access_token_property(self, test_credential):
        # should indicate presence of access token
        # already has token from fixture
        assert test_credential.has_access_token is True
        
        # removing token
        test_credential.set_access_token('')
        test_credential.save()
        assert test_credential.has_access_token is False
    
    def test_repositories_count_property(self, test_credential, test_repository):
        # should count repositories using this credential
        count = test_credential.repositories_count
        assert count == 1
    
    def test_unique_constraint_tenant_name(self, test_credential):
        # should enforce unique (tenant, name) constraint
        with pytest.raises(IntegrityError):
            TenantCredential.objects.create(
                tenant=test_credential.tenant,
                name=test_credential.name,  # duplicate name
                provider=TenantCredential.PROVIDER_GITHUB,
                added_by=test_credential.added_by
            )
    
    def test_str_representation(self, test_credential):
        # should return formatted string
        expected = f"{test_credential.name} ({test_credential.provider}) - {test_credential.tenant.name}"
        assert str(test_credential) == expected


@pytest.mark.django_db
class TestRepositoryModel:
    # testing Repository model
    
    def test_repository_creation_success(self, db, test_tenant, test_credential):
        # should create repository successfully
        repo = Repository.objects.create(
            tenant=test_tenant,
            name="test-repo",
            url="https://github.com/user/test-repo",
            default_branch="main",
            description="Test repository",
            credential=test_credential
        )
        assert repo.name == "test-repo"
        assert repo.default_branch == "main"
    
    def test_unique_constraint_tenant_url(self, test_repository):
        # should enforce unique (tenant, url) constraint
        with pytest.raises(IntegrityError):
            Repository.objects.create(
                tenant=test_repository.tenant,
                name="different-name",
                url=test_repository.url,  # duplicate URL
                credential=test_repository.credential
            )
    
    def test_str_representation(self, test_repository):
        # should return formatted string
        expected = f"{test_repository.name} ({test_repository.tenant.name})"
        assert str(test_repository) == expected
    
    def test_repository_without_credential(self, db, test_tenant):
        # should allow repository without credential (nullable)
        repo = Repository.objects.create(
            tenant=test_tenant,
            name="public-repo",
            url="https://github.com/user/public-repo"
        )
        assert repo.credential is None


@pytest.mark.django_db
class TestRepositoryAssignmentModel:
    # testing RepositoryAssignment model
    
    def test_assignment_creation_success(self, test_repository, test_developer_member, test_user):
        # should create assignment successfully
        assignment = RepositoryAssignment.objects.create(
            repository=test_repository,
            member=test_developer_member,
            assigned_by=test_user
        )
        assert assignment.repository == test_repository
        assert assignment.member == test_developer_member
    
    def test_unique_constraint_repository_member(self, test_repository, test_developer_member, test_user):
        # should enforce unique (repository, member) constraint
        RepositoryAssignment.objects.create(
            repository=test_repository,
            member=test_developer_member,
            assigned_by=test_user
        )
        
        with pytest.raises(IntegrityError):
            RepositoryAssignment.objects.create(
                repository=test_repository,
                member=test_developer_member,  # duplicate assignment
                assigned_by=test_user
            )
    
    def test_str_representation(self, test_repository, test_developer_member, test_user):
        # should return formatted string
        assignment = RepositoryAssignment.objects.create(
            repository=test_repository,
            member=test_developer_member,
            assigned_by=test_user
        )
        expected = f"{test_developer_member.user.email} → {test_repository.name}"
        assert str(assignment) == expected
