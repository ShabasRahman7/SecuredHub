"""
Repository management views.
Provides endpoints for creating, listing, and managing repositories within organizations.
"""
from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import IntegrityError

from accounts.models import Tenant
from .models import Repository
from .serializers import (
    RepositorySerializer,
    RepositoryCreateSerializer,
    RepositoryUpdateSerializer
)
from .utils import user_has_tenant_access, user_is_tenant_owner

import logging

logger = logging.getLogger('api')


# ============ Repository Management ============

@extend_schema(
    summary="Create Repository",
    description="Create a new repository in an organization. Both owners and developers can add repositories.",
    request=RepositoryCreateSerializer,
    responses={201: RepositorySerializer},
    tags=["Repositories"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_repository(request, tenant_id):
    """
    Create a new repository in a tenant.
    Both owners and developers can add repositories.
    
    POST /api/v1/tenants/{tenant_id}/repositories/create/
    Body: {
        "name": "My Project",
        "url": "https://github.com/owner/repo",
        "visibility": "private",
        "default_branch": "main"
    }
    """
    user = request.user
    
    # Get tenant
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user has access to this tenant
    if not user_has_tenant_access(user, tenant):
        logger.warning(f"Unauthorized repository creation attempt by user {user.id} for tenant {tenant_id}")
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "You must be a member of this tenant to add repositories."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validate and create repository
    serializer = RepositoryCreateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            repo = serializer.save(tenant=tenant)
            logger.info(f"Repository '{repo.name}' created by user {user.id} in tenant {tenant_id}")
            
            return Response(
                {
                    "success": True,
                    "message": "Repository created successfully",
                    "repository": RepositorySerializer(repo).data
                },
                status=status.HTTP_201_CREATED
            )
        except IntegrityError:
            logger.error(f"Duplicate repository URL for tenant {tenant_id}: {request.data.get('url')}")
            return Response(
                {
                    "success": False,
                    "error": {
                        "message": "Repository already exists",
                        "details": "This repository URL has already been added to this tenant."
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(
        {
            "success": False,
            "error": {
                "message": "Validation failed",
                "details": serializer.errors
            }
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@extend_schema(
    summary="List Repositories",
    description="List all repositories in a tenant. Only tenant members can view repositories.",
    parameters=[
        OpenApiParameter(name="is_active", description="Filter by active status", required=False, type=OpenApiTypes.BOOL),
        OpenApiParameter(name="visibility", description="Filter by visibility (public/private)", required=False, type=OpenApiTypes.STR),
    ],
    responses={200: RepositorySerializer(many=True)},
    tags=["Repositories"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_repositories(request, tenant_id):
    """
    List all repositories in a tenant.
    Only tenant members can view repositories.
    
    GET /api/v1/tenants/{tenant_id}/repositories/
    
    Query Parameters:
    - is_active: Filter by active status (true/false)
    - visibility: Filter by visibility (public/private)
    """
    user = request.user
    
    # Get tenant
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user has access to this tenant
    if not user_has_tenant_access(user, tenant):
        logger.warning(f"Unauthorized repository list access by user {user.id} for tenant {tenant_id}")
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "You must be a member of this tenant to view repositories."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get repositories
    repositories = tenant.repositories.all()
    
    # Filter for developers: only show assigned repositories
    if not user_is_tenant_owner(user, tenant):
        repositories = repositories.filter(assigned_developers=user)
    
    # Apply filters
    is_active = request.query_params.get('is_active')
    if is_active is not None:
        is_active_bool = is_active.lower() == 'true'
        repositories = repositories.filter(is_active=is_active_bool)
    
    visibility = request.query_params.get('visibility')
    if visibility in ['public', 'private']:
        repositories = repositories.filter(visibility=visibility)
    
    serializer = RepositorySerializer(repositories, many=True)
    
    logger.info(f"User {user.id} listed {repositories.count()} repositories for tenant {tenant_id}")
    
    return Response(
        {
            "success": True,
            "count": repositories.count(),
            "repositories": serializer.data
        },
        status=status.HTTP_200_OK
    )


@extend_schema(
    summary="Get Repository",
    description="Get details of a specific repository.",
    responses={200: RepositorySerializer},
    tags=["Repositories"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_repository(request, tenant_id, repo_id):
    """
    Get details of a specific repository.
    
    GET /api/v1/tenants/{tenant_id}/repositories/{repo_id}/
    """
    user = request.user
    
    # Get tenant
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user has access to this tenant
    if not user_has_tenant_access(user, tenant):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "You must be a member of this tenant."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get repository
    repository = get_object_or_404(Repository, id=repo_id, tenant=tenant)
    
    serializer = RepositorySerializer(repository)
    
    return Response(
        {
            "success": True,
            "repository": serializer.data
        },
        status=status.HTTP_200_OK
    )


@extend_schema(
    summary="Update Repository",
    description="Update repository details (owners and developers can update).",
    request=RepositoryUpdateSerializer,
    responses={200: RepositorySerializer},
    tags=["Repositories"]
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_repository(request, tenant_id, repo_id):
    """
    Update repository details (owners and developers can update).
    
    PUT/PATCH /api/v1/tenants/{tenant_id}/repositories/{repo_id}/
    Body: {
        "name": "Updated Name",
        "visibility": "public",
        "is_active": true
    }
    """
    user = request.user
    
    # Get tenant
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user has access to this tenant
    if not user_has_tenant_access(user, tenant):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "You must be a member of this tenant."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get repository
    repository = get_object_or_404(Repository, id=repo_id, tenant=tenant)
    
    # Update repository
    serializer = RepositoryUpdateSerializer(repository, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        logger.info(f"Repository {repo_id} updated by user {user.id}")
        
        return Response(
            {
                "success": True,
                "message": "Repository updated successfully",
                "repository": RepositorySerializer(repository).data
            },
            status=status.HTTP_200_OK
        )
    
    return Response(
        {
            "success": False,
            "error": {
                "message": "Validation failed",
                "details": serializer.errors
            }
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@extend_schema(
    summary="Delete Repository",
    description="Delete a repository (owner only).",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Repositories"]
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_repository(request, tenant_id, repo_id):
    """
    Delete a repository (owner only).
    
    DELETE /api/v1/tenants/{tenant_id}/repositories/{repo_id}/
    """
    user = request.user
    
    # Get tenant
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user is owner of this tenant
    if not user_is_tenant_owner(user, tenant):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "Only tenant owners can delete repositories."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get repository
    repository = get_object_or_404(Repository, id=repo_id, tenant=tenant)
    
    repo_name = repository.name
    repository.delete()
    
    logger.info(f"Repository '{repo_name}' (ID: {repo_id}) deleted by user {user.id}")
    
    return Response(
        {
            "success": True,
            "message": f"Repository '{repo_name}' deleted successfully"
        },
        status=status.HTTP_200_OK
    )
