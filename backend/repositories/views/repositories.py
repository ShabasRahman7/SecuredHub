from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiTypes

from accounts.models import Tenant, TenantMember
from accounts.permissions import IsTenantMember, IsTenantOwner
from repositories.models import Repository, RepositoryAssignment, TenantCredential
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
        
        url = serializer.validated_data.get('url')
        
        github_credential = TenantCredential.objects.filter(
            tenant=tenant,
            provider='github',
            is_active=True
        ).first()
        
        existing_inactive = Repository.objects.filter(tenant=tenant, url=url, is_active=False).first()
        
        if existing_inactive:
            existing_inactive.name = serializer.validated_data.get('name', existing_inactive.name)
            existing_inactive.default_branch = serializer.validated_data.get('default_branch', 'main')
            existing_inactive.description = serializer.validated_data.get('description', '')
            existing_inactive.credential = github_credential
            existing_inactive.is_active = True
            existing_inactive.webhook_id = None
            existing_inactive.webhook_secret = None
            existing_inactive.save()
            repository = existing_inactive
        else:
            repository = serializer.save(tenant=tenant, credential=github_credential)
        
        self._setup_webhook(repository)
        
        return Response({
            "success": True,
            "message": "Repository created successfully",
            "repository": RepositorySerializer(repository).data
        }, status=status.HTTP_201_CREATED)
    
    def _setup_webhook(self, repository):
        from django.conf import settings
        from webhooks.github_api import create_webhook, generate_webhook_secret
        
        if not repository.credential:
            return
        
        access_token = repository.credential.get_access_token()
        if not access_token:
            return
        
        webhook_url = f"{settings.WEBHOOK_BASE_URL}/api/v1/webhooks/github/"
        webhook_secret = generate_webhook_secret()
        
        webhook_id = create_webhook(
            repository.url,
            access_token,
            webhook_url,
            webhook_secret
        )
        
        if webhook_id:
            repository.webhook_id = webhook_id
            repository.webhook_secret = webhook_secret
            repository.save(update_fields=['webhook_id', 'webhook_secret'])

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
        
        self._cleanup_webhook(repository)
        
        repository.is_active = False
        repository.webhook_id = None
        repository.webhook_secret = None
        repository.save()
        
        return Response({
            "success": True,
            "message": "Repository deleted successfully"
        }, status=status.HTTP_200_OK)
    
    def _cleanup_webhook(self, repository):
        from webhooks.github_api import delete_webhook
        
        if not repository.webhook_id or not repository.credential:
            return
        
        access_token = repository.credential.get_access_token()
        if not access_token:
            return
        
        delete_webhook(repository.url, access_token, repository.webhook_id)

list_repositories = RepositoryListView.as_view()
create_repository = RepositoryCreateView.as_view()
delete_repository = RepositoryDeleteView.as_view()
