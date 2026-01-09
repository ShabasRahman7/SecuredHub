# shared pytest fixtures for all Django tests
import pytest
from faker import Faker
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch

User = get_user_model()
fake = Faker()


# user fixtures
@pytest.fixture
def test_user(db):
    # creating a standard test user
    return User.objects.create_user(
        email=fake.email(),
        password='testpass123'
    )


@pytest.fixture
def test_admin(db):
    # creating an admin/staff user
    return User.objects.create_superuser(
        email=fake.email(),
        password='adminpass123'
    )


# tenant fixtures
@pytest.fixture
def test_tenant(db, test_user):
    # creating a test tenant/organization
    from accounts.models import Tenant
    return Tenant.objects.create(
        name=fake.company(),
        created_by=test_user,
        description=fake.text(max_nb_chars=200)
    )


@pytest.fixture
def test_owner_member(db, test_tenant, test_user):
    # creating a tenant member with owner role
    from accounts.models import TenantMember
    return TenantMember.objects.create(
        tenant=test_tenant,
        user=test_user,
        role=TenantMember.ROLE_OWNER
    )


@pytest.fixture
def test_developer_member(db, test_tenant):
    # creating a tenant member with developer role
    from accounts.models import TenantMember
    dev_user = User.objects.create_user(
        email=fake.email(),
        password='devpass123'
    )
    return TenantMember.objects.create(
        tenant=test_tenant,
        user=dev_user,
        role=TenantMember.ROLE_DEVELOPER
    )


# repository fixtures
@pytest.fixture
def test_credential(db, test_tenant, test_user):
    # creating a test tenant credential with encrypted token
    from repositories.models import TenantCredential
    credential = TenantCredential.objects.create(
        tenant=test_tenant,
        name=f"{fake.word()}_credential",
        provider=TenantCredential.PROVIDER_GITHUB,
        github_account_login=fake.user_name(),
        added_by=test_user
    )
    credential.set_access_token('test_token_12345')
    credential.save()
    return credential


@pytest.fixture
def test_repository(db, test_tenant, test_credential):
    # creating a test repository
    from repositories.models import Repository
    return Repository.objects.create(
        tenant=test_tenant,
        name=fake.slug(),
        url=f"https://github.com/{fake.user_name()}/{fake.slug()}",
        default_branch='main',
        description=fake.text(max_nb_chars=100),
        credential=test_credential
    )


# redis/cache mocking
@pytest.fixture
def mock_redis_cache(mocker):
    # mocking Django cache (Redis) operations
    mock_cache = {}
    
    def mock_get(key):
        return mock_cache.get(key)
    
    def mock_set(key, value, timeout=None):
        mock_cache[key] = value
    
    def mock_delete(key):
        mock_cache.pop(key, None)
    
    cache_mock = mocker.patch('django.core.cache.cache')
    cache_mock.get.side_effect = mock_get
    cache_mock.set.side_effect = mock_set
    cache_mock.delete.side_effect = mock_delete
    
    return cache_mock


# email mocking
@pytest.fixture
def mock_send_mail(mocker):
    # mocking email sending
    return mocker.patch('django.core.mail.send_mail', return_value=1)


# scan finding fixture (for chat tests)
@pytest.fixture
def test_scan_finding(db, test_repository):
    # creating a test scan finding
    from scans.models import Scan, ScanFinding
    
    scan = Scan.objects.create(
        repository=test_repository,
        status='completed'
    )
    
    return ScanFinding.objects.create(
        scan=scan,
        scanner_type='bandit',
        severity='HIGH',
        title='SQL Injection Risk',
        description='Potential SQL injection vulnerability detected',
        file_path='app/views.py',
        line_number=42
    )
