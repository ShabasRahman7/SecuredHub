import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(email='dev@test.com', password='pass123')


@pytest.fixture
def admin(db):
    return User.objects.create_superuser(email='admin@test.com', password='admin123')


@pytest.fixture
def tenant(db, user):
    from accounts.models import Tenant
    return Tenant.objects.create(name='Acme Corp', created_by=user)


@pytest.fixture
def owner_member(db, tenant, user):
    from accounts.models import TenantMember
    return TenantMember.objects.create(tenant=tenant, user=user, role='owner')


@pytest.fixture
def developer(db, tenant):
    from accounts.models import TenantMember
    dev = User.objects.create_user(email='developer@test.com', password='dev123')
    return TenantMember.objects.create(tenant=tenant, user=dev, role='developer')


@pytest.fixture
def credential(db, tenant, user):
    from repositories.models import TenantCredential
    cred = TenantCredential.objects.create(
        tenant=tenant,
        name='github_token',
        provider='github',
        github_account_login='testuser',
        added_by=user
    )
    cred.set_access_token('ghp_test123')
    cred.save()
    return cred


@pytest.fixture
def repository(db, tenant, credential):
    from repositories.models import Repository
    return Repository.objects.create(
        tenant=tenant,
        name='my-repo',
        url='https://github.com/testuser/my-repo',
        default_branch='main',
        credential=credential
    )


@pytest.fixture
def scan(db, repository, user):
    from scans.models import Scan
    return Scan.objects.create(
        repository=repository,
        triggered_by=user,
        status='completed',
        commit_hash='abc123'
    )


@pytest.fixture
def finding(db, scan):
    from scans.models import ScanFinding
    return ScanFinding.objects.create(
        scan=scan,
        tool='semgrep',
        rule_id='hardcoded-password',
        title='Hardcoded Password',
        description='Password found in source code',
        severity='high',
        file_path='config.py',
        line_number=10
    )
