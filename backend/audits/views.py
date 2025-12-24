"""
Views for audit log API endpoints.

Provides read-only access to audit logs for organization owners.
"""
from rest_framework import generics, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from accounts.models import TenantMember
from .models import AuditLog, EvaluationEvidence
from .serializers import AuditLogSerializer, EvaluationEvidenceSerializer


class IsOrganizationOwner(permissions.BasePermission):
    """
    Permission check for organization owners.
    Only owners can access audit logs.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Admins can access all audit logs
        if request.user.is_staff:
            return True
        
        # Check if user is an owner of any organization
        return TenantMember.objects.filter(
            user=request.user,
            role='owner',
            deleted_at__isnull=True
        ).exists()


class AuditLogListView(generics.ListAPIView):
    """
    List audit logs for the user's organization.
    
    Only organization owners and platform admins can access this endpoint.
    Logs are filtered by the user's organization.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationOwner]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admins can filter by organization_id parameter
        if user.is_staff:
            org_id = self.request.query_params.get('organization_id')
            if org_id:
                return AuditLog.objects.filter(organization_id=org_id).select_related(
                    'actor', 'content_type'
                )
            return AuditLog.objects.all().select_related('actor', 'content_type')
        
        # Get user's organization
        membership = TenantMember.objects.filter(
            user=user,
            deleted_at__isnull=True
        ).first()
        
        if not membership:
            return AuditLog.objects.none()
        
        return AuditLog.objects.filter(
            organization=membership.tenant
        ).select_related('actor', 'content_type')


class AuditLogDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single audit log with its evidence.
    
    Only organization owners and platform admins can access this endpoint.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationOwner]
    lookup_field = 'pk'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return AuditLog.objects.all().select_related('actor', 'content_type')
        
        membership = TenantMember.objects.filter(
            user=user,
            deleted_at__isnull=True
        ).first()
        
        if not membership:
            return AuditLog.objects.none()
        
        return AuditLog.objects.filter(
            organization=membership.tenant
        ).select_related('actor', 'content_type')
