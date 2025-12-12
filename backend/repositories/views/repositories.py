"""Simple repository management views."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from accounts.models import Tenant
from repositories.models import Repository


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_repositories(request, tenant_id):
    """List repositories in a tenant."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user belongs to tenant
    if not hasattr(user, 'tenant_membership') or user.tenant_membership.tenant != tenant:
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    
    repositories = tenant.repositories.filter(is_active=True)
    
    data = []
    for repo in repositories:
        data.append({
            'id': repo.id,
            'name': repo.name,
            'url': repo.url,
            'default_branch': repo.default_branch,
            'description': repo.description,
            'created_at': repo.created_at,
        })
    
    return Response({'repositories': data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_repository(request, tenant_id):
    """Create a new repository."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user belongs to tenant
    if not hasattr(user, 'tenant_membership') or user.tenant_membership.tenant != tenant:
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    
    name = request.data.get('name')
    url = request.data.get('url')
    default_branch = request.data.get('default_branch', 'main')
    description = request.data.get('description', '')
    
    if not name or not url:
        return Response({"error": "Name and URL are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if repository already exists
    if Repository.objects.filter(tenant=tenant, url=url).exists():
        return Response({"error": "Repository already exists"}, status=status.HTTP_400_BAD_REQUEST)
    
    repository = Repository.objects.create(
        tenant=tenant,
        name=name,
        url=url,
        default_branch=default_branch,
        description=description
    )
    
    return Response({
        'id': repository.id,
        'name': repository.name,
        'url': repository.url,
        'default_branch': repository.default_branch,
        'description': repository.description,
        'created_at': repository.created_at,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_repository(request, tenant_id, repo_id):
    """Get repository details."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user belongs to tenant
    if not hasattr(user, 'tenant_membership') or user.tenant_membership.tenant != tenant:
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    
    repository = get_object_or_404(Repository, id=repo_id, tenant=tenant)
    
    return Response({
        'id': repository.id,
        'name': repository.name,
        'url': repository.url,
        'default_branch': repository.default_branch,
        'description': repository.description,
        'created_at': repository.created_at,
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_repository(request, tenant_id, repo_id):
    """Delete a repository."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user is owner
    if not hasattr(user, 'tenant_membership') or user.tenant_membership.tenant != tenant or user.tenant_membership.role != 'owner':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    
    repository = get_object_or_404(Repository, id=repo_id, tenant=tenant)
    repository.delete()
    
    return Response({"message": "Repository deleted successfully"})