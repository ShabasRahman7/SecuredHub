from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsTenantOwner(BasePermission):
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
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        from .models import TenantMember
        return TenantMember.objects.filter(
            tenant=obj,
            user=request.user
        ).exists()
