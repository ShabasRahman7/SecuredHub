# unit tests for accounts app permissions
import pytest
from unittest.mock import Mock
from accounts.permissions import IsAdmin, IsTenantOwner, IsTenantMember
from accounts.models import TenantMember


@pytest.mark.django_db
class TestIsAdmin:
    # testing IsAdmin permission class
    
    def test_allows_staff_user(self, test_admin):
        # should allow authenticated staff users
        permission = IsAdmin()
        request = Mock(user=test_admin)
        view = Mock()
        
        assert permission.has_permission(request, view) is True
    
    def test_denies_non_staff_user(self, test_user):
        # should deny non-staff users
        permission = IsAdmin()
        request = Mock(user=test_user)
        view = Mock()
        
        assert permission.has_permission(request, view) is False
    
    def test_denies_unauthenticated_user(self):
        # should deny unauthenticated users
        permission = IsAdmin()
        mock_user = Mock(is_authenticated=False, is_staff=False)
        request = Mock(user=mock_user)
        view = Mock()
        
        assert permission.has_permission(request, view) is False


@pytest.mark.django_db
class TestIsTenantOwner:
    # testing IsTenantOwner permission class - enforces tenant isolation
    
    def test_allows_tenant_owner(self, test_owner_member):
        # should allow owner of the tenant
        permission = IsTenantOwner()
        request = Mock(user=test_owner_member.user)
        view = Mock()
        
        assert permission.has_object_permission(
            request, view, test_owner_member.tenant
        ) is True
    
    def test_denies_developer_member(self, test_developer_member):
        # should deny developer (non-owner) of the tenant
        permission = IsTenantOwner()
        request = Mock(user=test_developer_member.user)
        view = Mock()
        
        assert permission.has_object_permission(
            request, view, test_developer_member.tenant
        ) is False
    
    def test_denies_cross_tenant_owner(self, db, test_user, test_tenant):
        # CRITICAL: should deny owner of different tenant (tenant isolation)
        # creating a different tenant with different owner
        from accounts.models import Tenant
        other_tenant = Tenant.objects.create(
            name="Other Company",
            created_by=test_user
        )
        TenantMember.objects.create(
            tenant=other_tenant,
            user=test_user,
            role=TenantMember.ROLE_OWNER
        )
        
        permission = IsTenantOwner()
        request = Mock(user=test_user)
        view = Mock()
        
        # trying to access test_tenant (should be denied)
        assert permission.has_object_permission(
            request, view, test_tenant
        ) is False
    
    def test_denies_non_member(self, db, test_user, test_tenant):
        # should deny users who are not members of the tenant
        permission = IsTenantOwner()
        request = Mock(user=test_user)
        view = Mock()
        
        assert permission.has_object_permission(
            request, view, test_tenant
        ) is False
    
    def test_denies_unauthenticated_user(self, test_tenant):
        # should deny unauthenticated users
        permission = IsTenantOwner()
        mock_user = Mock(is_authenticated=False)
        request = Mock(user=mock_user)
        view = Mock()
        
        assert permission.has_object_permission(
            request, view, test_tenant
        ) is False


@pytest.mark.django_db
class TestIsTenantMember:
    # testing IsTenantMember permission class - enforces tenant isolation
    
    def test_allows_owner_member(self, test_owner_member):
        # should allow owner member
        permission = IsTenantMember()
        request = Mock(user=test_owner_member.user)
        view = Mock()
        
        assert permission.has_object_permission(
            request, view, test_owner_member.tenant
        ) is True
    
    def test_allows_developer_member(self, test_developer_member):
        # should allow developer member
        permission = IsTenantMember()
        request = Mock(user=test_developer_member.user)
        view = Mock()
        
        assert permission.has_object_permission(
            request, view, test_developer_member.tenant
        ) is True
    
    def test_denies_cross_tenant_member(self, db, test_user, test_tenant):
        # CRITICAL: should deny member of different tenant (tenant isolation)
        # creating a different tenant
        from accounts.models import Tenant
        other_tenant = Tenant.objects.create(
            name="Other Company",
            created_by=test_user
        )
        TenantMember.objects.create(
            tenant=other_tenant,
            user=test_user,
            role=TenantMember.ROLE_DEVELOPER
        )
        
        permission = IsTenantMember()
        request = Mock(user=test_user)
        view = Mock()
        
        # trying to access test_tenant (should be denied)
        assert permission.has_object_permission(
            request, view, test_tenant
        ) is False
    
    def test_denies_non_member(self, db, test_user, test_tenant):
        # should deny users who are not members
        permission = IsTenantMember()
        request = Mock(user=test_user)
        view = Mock()
        
        assert permission.has_object_permission(
            request, view, test_tenant
        ) is False
    
    def test_denies_unauthenticated_user(self, test_tenant):
        # should deny unauthenticated users
        permission = IsTenantMember()
        mock_user = Mock(is_authenticated=False)
        request = Mock(user=mock_user)
        view = Mock()
        
        assert permission.has_object_permission(
            request, view, test_tenant
        ) is False
