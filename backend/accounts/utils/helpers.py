"""
Utility functions for organization/tenant permissions.
"""
from ..models import TenantMember, Tenant


def user_has_tenant_access(user, tenant):
    """Check if user is a member (owner or developer) of the tenant."""
    return TenantMember.objects.filter(
        user=user,
        tenant=tenant
    ).exists()


def user_is_tenant_owner(user, tenant):
    """Check if user is an owner of the tenant."""
    return TenantMember.objects.filter(
        user=user,
        tenant=tenant,
        role=TenantMember.ROLE_OWNER
    ).exists()


def user_is_tenant_member(user, tenant, role=None):
    """Check if user is a member with optional role filter."""
    query = TenantMember.objects.filter(
        user=user,
        tenant=tenant
    )
    
    if role:
        query = query.filter(role=role)
    
    return query.exists()


def get_user_tenants(user):
    """Get all tenants where user is a member."""
    return Tenant.objects.filter(
        members__user=user
    ).distinct()
