from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiTypes

from accounts.models import Tenant, TenantMember
from accounts.permissions import IsTenantMember, IsTenantOwner
from repositories.models import Repository, RepositoryAssignment
from repositories.serializers import RepositorySerializer, RepositoryCreateSerializer

class RepositoryListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantMember]

    @extend_schema(
        summary="List Repositories",
        responses={200: RepositorySerializer(many=True)},
        tags=["Repositories"]
    )
    def get(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        try:
            member = TenantMember.objects.get(user=request.user, tenant=tenant)
            if member.role == TenantMember.ROLE_DEVELOPER:
                assignments = RepositoryAssignment.objects.filter(member=member)
                repository_ids = [a.repository.id for a in assignments]
                repositories = tenant.repositories.filter(id__in=repository_ids, is_active=True)
            else:
                repositories = tenant.repositories.filter(is_active=True)
        except TenantMember.DoesNotExist:
            repositories = tenant.repositories.filter(is_active=True)
        
        serializer = RepositorySerializer(repositories, many=True)
        
        return Response({'repositories': serializer.data}, status=status.HTTP_200_OK)

class RepositoryCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Create Repository",
        request=RepositoryCreateSerializer,
        responses={201: RepositorySerializer},
        tags=["Repositories"]
    )
    def post(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        serializer = RepositoryCreateSerializer(data=request.data, context={'tenant': tenant})
        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": {
                    "message": "Validation failed",
                    "details": serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        repository = serializer.save(tenant=tenant)
        
        return Response({
            "success": True,
            "message": "Repository created successfully",
            "repository": RepositorySerializer(repository).data
        }, status=status.HTTP_201_CREATED)

class RepositoryDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Delete Repository",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Repositories"]
    )
    def delete(self, request, tenant_id, repo_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        repository = get_object_or_404(Repository, id=repo_id, tenant=tenant)
        
        repository.is_active = False
        repository.save()
        
        return Response({
            "success": True,
            "message": "Repository deleted successfully"
        }, status=status.HTTP_200_OK)

list_repositories = RepositoryListView.as_view()
create_repository = RepositoryCreateView.as_view()
delete_repository = RepositoryDeleteView.as_view()
