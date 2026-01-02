"""
Utility functions for organization/tenant permissions.
"""
from ..models import TenantMember, Tenant

def user_has_tenant_access(user, tenant):
    return TenantMember.objects.filter(
        user=user,
        tenant=tenant
    ).exists()

def user_is_tenant_owner(user, tenant):
    return TenantMember.objects.filter(
        user=user,
        tenant=tenant,
        role=TenantMember.ROLE_OWNER
    ).exists()

def user_is_tenant_member(user, tenant, role=None):
    query = TenantMember.objects.filter(
        user=user,
        tenant=tenant
    )
    
    if role:
        query = query.filter(role=role)
    
    return query.exists()

def get_user_tenants(user):
    return Tenant.objects.filter(
        members__user=user
    ).distinct()
