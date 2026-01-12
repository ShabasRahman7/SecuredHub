import pytest
from django.db import IntegrityError
from accounts.models import User, Tenant, TenantMember


@pytest.mark.django_db
class TestUser:
    
    def test_create_user(self):
        user = User.objects.create_user(email='test@example.com', password='secret')
        assert user.email == 'test@example.com'
        assert user.check_password('secret')
        assert not user.is_staff
    
    def test_create_superuser(self):
        admin = User.objects.create_superuser(email='admin@example.com', password='admin')
        assert admin.is_staff
        assert admin.is_superuser
    
    def test_email_is_required(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email='', password='pass')
    
    def test_email_must_be_unique(self, user):
        with pytest.raises(IntegrityError):
            User.objects.create_user(email=user.email, password='another')


@pytest.mark.django_db
class TestTenant:
    
    def test_tenant_gets_slug(self, user):
        tenant = Tenant.objects.create(name='My Company', created_by=user)
        assert tenant.slug
    
    def test_soft_delete(self, tenant):
        tenant.soft_delete()
        tenant.refresh_from_db()
        assert tenant.is_deleted
        assert tenant.deleted_at is not None
    
    def test_restore(self, tenant):
        tenant.soft_delete()
        tenant.restore()
        tenant.refresh_from_db()
        assert not tenant.is_deleted


@pytest.mark.django_db
class TestTenantMember:
    
    def test_owner_role(self, owner_member):
        assert owner_member.is_owner()
        assert not owner_member.is_developer()
    
    def test_developer_role(self, developer):
        assert developer.is_developer()
        assert not developer.is_owner()
    
    def test_unique_user_per_tenant(self, owner_member):
        with pytest.raises(IntegrityError):
            TenantMember.objects.create(
                tenant=owner_member.tenant,
                user=owner_member.user,
                role='developer'
            )
