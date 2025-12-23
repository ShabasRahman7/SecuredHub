"""
API views for standards.
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404

from standards.models import ComplianceStandard, ComplianceRule, RepositoryStandard
from standards.serializers.standard import (
    ComplianceStandardListSerializer,
    ComplianceStandardDetailSerializer,
    ComplianceRuleSerializer,
    RepositoryStandardSerializer,
    AssignStandardSerializer
)
from repositories.models import Repository
from accounts.models import TenantMember


class StandardListView(generics.ListAPIView):
    """
    List all available compliance standards.
    
    Shows both built-in and organization-specific standards.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ComplianceStandardListSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Get user's tenant
        membership = TenantMember.objects.filter(
            user=user, 
            deleted_at__isnull=True
        ).first()
        
        # Show built-in standards + org-specific standards
        queryset = ComplianceStandard.objects.filter(is_active=True)
        
        if membership:
            queryset = queryset.filter(
                is_builtin=True
            ) | queryset.filter(
                organization=membership.tenant
            )
        else:
            # Admin or no tenant - show built-in only
            queryset = queryset.filter(is_builtin=True)
        
        # Annotate with rule count and total weight
        queryset = queryset.annotate(
            rule_count=Count('rules', filter=models.Q(rules__is_active=True)),
            total_weight=Sum('rules__weight', filter=models.Q(rules__is_active=True))
        )
        
        return queryset.distinct().order_by('name')


class StandardDetailView(generics.RetrieveAPIView):
    """
    Get details of a specific compliance standard including all rules.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ComplianceStandardDetailSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        return ComplianceStandard.objects.filter(is_active=True).prefetch_related(
            'rules'
        ).annotate(
            rule_count=Count('rules', filter=models.Q(rules__is_active=True)),
            total_weight=Sum('rules__weight', filter=models.Q(rules__is_active=True))
        )


class StandardRulesView(generics.ListAPIView):
    """
    List all rules for a specific standard.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ComplianceRuleSerializer
    
    def get_queryset(self):
        standard_slug = self.kwargs.get('slug')
        return ComplianceRule.objects.filter(
            standard__slug=standard_slug,
            is_active=True
        ).order_by('order', 'name')


class RepositoryStandardsView(generics.ListCreateAPIView):
    """
    List standards assigned to a repository or assign a new standard.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RepositoryStandardSerializer
    
    def get_queryset(self):
        repository_id = self.kwargs.get('repository_id')
        return RepositoryStandard.objects.filter(
            repository_id=repository_id,
            is_active=True
        ).select_related('standard', 'assigned_by')
    
    def create(self, request, repository_id):
        """Assign a standard to the repository."""
        user = request.user
        
        # Verify user has access to this repository (via tenant membership)
        repository = get_object_or_404(Repository, id=repository_id)
        
        membership = TenantMember.objects.filter(
            user=user,
            tenant=repository.tenant,
            deleted_at__isnull=True
        ).first()
        
        if not membership and not user.is_staff:
            return Response(
                {'error': 'You do not have access to this repository'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only owners can assign standards
        if membership and membership.role != 'owner' and not user.is_staff:
            return Response(
                {'error': 'Only owners can assign standards'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AssignStandardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        standard_id = serializer.validated_data['standard_id']
        
        # Check if already assigned
        existing = RepositoryStandard.objects.filter(
            repository=repository,
            standard_id=standard_id
        ).first()
        
        if existing:
            if existing.is_active:
                return Response(
                    {'error': 'Standard already assigned to this repository'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Reactivate
                existing.is_active = True
                existing.assigned_by = user
                existing.save()
                response_serializer = RepositoryStandardSerializer(existing)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        # Create assignment
        assignment = RepositoryStandard.objects.create(
            repository=repository,
            standard_id=standard_id,
            assigned_by=user
        )
        
        response_serializer = RepositoryStandardSerializer(assignment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class RepositoryStandardDeleteView(generics.DestroyAPIView):
    """
    Remove a standard assignment from a repository.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RepositoryStandard.objects.filter(is_active=True)
    
    def delete(self, request, repository_id, standard_id):
        user = request.user
        
        assignment = get_object_or_404(
            RepositoryStandard,
            repository_id=repository_id,
            standard_id=standard_id,
            is_active=True
        )
        
        # Verify permission
        membership = TenantMember.objects.filter(
            user=user,
            tenant=assignment.repository.tenant,
            deleted_at__isnull=True
        ).first()
        
        if not membership and not user.is_staff:
            return Response(
                {'error': 'You do not have access to this repository'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete
        assignment.is_active = False
        assignment.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


# Need to import models for annotations
from django.db import models
