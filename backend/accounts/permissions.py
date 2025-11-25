from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """Only platform admins (is_staff=True) can access"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsTenantOwner(BasePermission):
    """Check if user is owner of the tenant"""
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        from .models import TenantMember
        try:
            membership = TenantMember.objects.get(
                tenant=obj,
                user=request.user
            )
            return membership.role == TenantMember.ROLE_OWNER
        except TenantMember.DoesNotExist:
            return False


class IsTenantMember(BasePermission):
    """Check if user is member of the tenant (owner or developer)"""
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        from .models import TenantMember
        return TenantMember.objects.filter(
            tenant=obj,
            user=request.user
        ).exists()
