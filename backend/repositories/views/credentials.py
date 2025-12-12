"""API views for credential management."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from accounts.models import Tenant
from repositories.models import TenantCredential
from repositories.serializers import CredentialSerializer, CredentialCreateSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_credentials(request, tenant_id):
    """List all credentials for a tenant."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user belongs to tenant
    if not hasattr(user, 'tenant_membership') or user.tenant_membership.tenant != tenant:
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    
    # Optimize query with prefetch and annotation for accurate counts
    from django.db.models import Count
    
    credentials = tenant.credentials.filter(is_active=True).annotate(
        repo_count=Count('repositories', distinct=True)
    ).prefetch_related('repositories')
    
    data = []
    for credential in credentials:
        credential_data = {
            'id': credential.id,
            'name': credential.name,
            'provider': credential.provider,
            'created_at': credential.created_at,
            'last_used_at': credential.last_used_at,
            'repositories_count': credential.repo_count,  # Use annotated count
            'is_active': credential.is_active,
        }
        
        # Add GitHub-specific fields
        if credential.provider == 'github':
            credential_data.update({
                'github_account_login': credential.github_account_login,
                'github_account_id': credential.github_account_id,
                'granted_scopes': credential.granted_scopes,
                'oauth_data': credential.oauth_data,
            })
        
        data.append(credential_data)
    
    return Response({'credentials': data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_credential(request, tenant_id):
    """Create a new credential."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user belongs to tenant and is owner
    if not hasattr(user, 'tenant_membership') or user.tenant_membership.tenant != tenant:
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    
    if user.tenant_membership.role != 'owner':
        return Response({"error": "Only owners can manage credentials"}, status=status.HTTP_403_FORBIDDEN)
    
    name = request.data.get('name')
    provider = request.data.get('provider')
    access_token = request.data.get('access_token')
    
    if not all([name, provider, access_token]):
        return Response({"error": "Name, provider, and access_token are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if credential name already exists for this tenant
    if TenantCredential.objects.filter(tenant=tenant, name=name).exists():
        return Response({"error": "Credential with this name already exists"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate provider
    valid_providers = [choice[0] for choice in TenantCredential.PROVIDER_CHOICES]
    if provider not in valid_providers:
        return Response({"error": "Invalid provider"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create credential
    credential = TenantCredential.objects.create(
        tenant=tenant,
        name=name,
        provider=provider,
        added_by=user
    )
    credential.set_access_token(access_token)
    credential.save()
    
    return Response({
        'id': credential.id,
        'name': credential.name,
        'provider': credential.provider,
        'created_at': credential.created_at,
        'is_active': credential.is_active,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_credential(request, tenant_id, credential_id):
    """Get credential details."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user belongs to tenant
    if not hasattr(user, 'tenant_membership') or user.tenant_membership.tenant != tenant:
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    
    credential = get_object_or_404(TenantCredential, id=credential_id, tenant=tenant)
    
    credential_data = {
        'id': credential.id,
        'name': credential.name,
        'provider': credential.provider,
        'created_at': credential.created_at,
        'last_used_at': credential.last_used_at,
        'repositories_count': credential.repositories_count,
        'is_active': credential.is_active,
    }
    
    # Add GitHub-specific fields
    if credential.provider == 'github':
        credential_data.update({
            'github_account_login': credential.github_account_login,
            'github_account_id': credential.github_account_id,
            'granted_scopes': credential.granted_scopes,
            'oauth_data': credential.oauth_data,
        })
    
    return Response(credential_data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_credential(request, tenant_id, credential_id):
    """Delete a credential."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user is owner
    if not hasattr(user, 'tenant_membership') or user.tenant_membership.tenant != tenant or user.tenant_membership.role != 'owner':
        return Response({"error": "Only owners can delete credentials"}, status=status.HTTP_403_FORBIDDEN)
    
    credential = get_object_or_404(TenantCredential, id=credential_id, tenant=tenant)
    
    # Check if credential is being used by repositories
    if credential.repositories_count > 0:
        return Response({
            "error": f"Cannot delete credential. It is being used by {credential.repositories_count} repositories."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    credential.delete()
    
    return Response({"message": "Credential deleted successfully"})


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_credential(request, tenant_id, credential_id):
    """Update a credential."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user is owner
    if not hasattr(user, 'tenant_membership') or user.tenant_membership.tenant != tenant or user.tenant_membership.role != 'owner':
        return Response({"error": "Only owners can update credentials"}, status=status.HTTP_403_FORBIDDEN)
    
    credential = get_object_or_404(TenantCredential, id=credential_id, tenant=tenant)
    
    name = request.data.get('name')
    access_token = request.data.get('access_token')
    is_active = request.data.get('is_active')
    
    if name and name != credential.name:
        # Check if new name already exists
        if TenantCredential.objects.filter(tenant=tenant, name=name).exclude(id=credential.id).exists():
            return Response({"error": "Credential with this name already exists"}, status=status.HTTP_400_BAD_REQUEST)
        credential.name = name
    
    if access_token:
        credential.set_access_token(access_token)
    
    if is_active is not None:
        credential.is_active = is_active
    
    credential.save()
    
    return Response({
        'id': credential.id,
        'name': credential.name,
        'provider': credential.provider,
        'is_active': credential.is_active,
    })