"""OAuth integration views."""
import requests
import json
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import base64

from accounts.models import Tenant
from repositories.models import TenantCredential


@csrf_exempt
@require_http_methods(["GET"])
def github_oauth_callback(request):
    """Handle GitHub OAuth callback."""
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    if error:
        # Redirect to frontend with error
        return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?error=oauth_denied")
    
    if not code or not state:
        return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?error=invalid_callback")
    
    try:
        # Decode state to get tenant_id and return_url
        state_data = json.loads(base64.b64decode(state).decode())
        tenant_id = state_data.get('tenant_id')
        return_url = state_data.get('return_url', '/tenant-dashboard')
        
        if not tenant_id:
            return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?error=invalid_state")
        
        # Exchange code for access token
        token_response = requests.post('https://github.com/login/oauth/access_token', {
            'client_id': settings.GITHUB_CLIENT_ID,
            'client_secret': settings.GITHUB_CLIENT_SECRET,
            'code': code,
        }, headers={
            'Accept': 'application/json'
        })
        
        if token_response.status_code != 200:
            return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?error=token_exchange_failed")
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        scope = token_data.get('scope', '')
        
        if not access_token:
            return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?error=no_access_token")
        
        # Get user/organization info from GitHub
        user_response = requests.get('https://api.github.com/user', headers={
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        })
        
        if user_response.status_code != 200:
            return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?error=github_api_failed")
        
        github_user = user_response.json()
        
        # Get organizations if scope includes read:org
        orgs = []
        if 'read:org' in scope:
            orgs_response = requests.get('https://api.github.com/user/orgs', headers={
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json'
            })
            if orgs_response.status_code == 200:
                orgs = orgs_response.json()
        
        # Store credential in database
        tenant = get_object_or_404(Tenant, id=tenant_id)
        
        # Check if GitHub credential already exists for this tenant
        existing_credential = TenantCredential.objects.filter(
            tenant=tenant,
            provider='github',
            github_account_id=str(github_user['id'])
        ).first()
        
        if existing_credential:
            # Update existing credential
            existing_credential.set_access_token(access_token)
            existing_credential.granted_scopes = scope
            existing_credential.github_account_login = github_user['login']
            existing_credential.oauth_data = {
                'github_user': github_user,
                'organizations': orgs,
                'token_type': token_data.get('token_type', 'bearer')
            }
            existing_credential.is_active = True
            existing_credential.save()
            credential = existing_credential
        else:
            # Create new credential
            credential = TenantCredential.objects.create(
                tenant=tenant,
                name=f"GitHub ({github_user['login']})",
                provider='github',
                github_account_id=str(github_user['id']),
                github_account_login=github_user['login'],
                granted_scopes=scope,
                oauth_data={
                    'github_user': github_user,
                    'organizations': orgs,
                    'token_type': token_data.get('token_type', 'bearer')
                }
            )
            credential.set_access_token(access_token)
            credential.save()
        
        # Redirect back to frontend with success
        return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?github_connected=true&credential_id={credential.id}")
        
    except Exception as e:
        print(f"GitHub OAuth error: {str(e)}")
        return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?error=oauth_processing_failed")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_github_credential(request, tenant_id, credential_id):
    """Revoke GitHub OAuth credential."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user is owner
    if not hasattr(user, 'tenant_membership') or user.tenant_membership.tenant != tenant or user.tenant_membership.role != 'owner':
        return Response({"error": "Only owners can revoke credentials"}, status=status.HTTP_403_FORBIDDEN)
    
    credential = get_object_or_404(TenantCredential, id=credential_id, tenant=tenant, provider='github')
    
    try:
        # Revoke token on GitHub
        access_token = credential.get_access_token()
        if access_token:
            revoke_response = requests.delete(
                f'https://api.github.com/applications/{settings.GITHUB_CLIENT_ID}/token',
                auth=(settings.GITHUB_CLIENT_ID, settings.GITHUB_CLIENT_SECRET),
                json={'access_token': access_token}
            )
            
            if revoke_response.status_code not in [204, 404]:
                return Response({
                    "error": "Failed to revoke token on GitHub"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Deactivate credential
        credential.is_active = False
        credential.save()
        
        return Response({"message": "GitHub credential revoked successfully"})
        
    except Exception as e:
        return Response({
            "error": f"Failed to revoke credential: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def github_repositories(request, tenant_id, credential_id):
    """Fetch repositories from GitHub using the credential."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Check if user belongs to tenant
    if not hasattr(user, 'tenant_membership') or user.tenant_membership.tenant != tenant:
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    
    credential = get_object_or_404(TenantCredential, id=credential_id, tenant=tenant, provider='github')
    
    if not credential.is_active:
        return Response({"error": "Credential is not active"}, status=status.HTTP_400_BAD_REQUEST)
    
    access_token = credential.get_access_token()
    if not access_token:
        return Response({"error": "No access token available"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Fetch user repositories
        repos_response = requests.get('https://api.github.com/user/repos', headers={
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }, params={
            'per_page': 100,
            'sort': 'updated',
            'affiliation': 'owner,collaborator,organization_member'
        })
        
        if repos_response.status_code != 200:
            return Response({
                "error": "Failed to fetch repositories from GitHub"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        repositories = repos_response.json()
        
        # Format repository data
        formatted_repos = []
        for repo in repositories:
            formatted_repos.append({
                'id': repo['id'],
                'name': repo['name'],
                'full_name': repo['full_name'],
                'description': repo['description'],
                'private': repo['private'],
                'html_url': repo['html_url'],
                'clone_url': repo['clone_url'],
                'default_branch': repo['default_branch'],
                'language': repo['language'],
                'stars_count': repo['stargazers_count'],
                'forks_count': repo['forks_count'],
                'updated_at': repo['updated_at'],
                'owner': {
                    'login': repo['owner']['login'],
                    'type': repo['owner']['type']
                }
            })
        
        # Update last used timestamp
        from django.utils import timezone
        credential.last_used_at = timezone.now()
        credential.save(update_fields=['last_used_at'])
        
        return Response({
            'repositories': formatted_repos,
            'total_count': len(formatted_repos)
        })
        
    except Exception as e:
        return Response({
            "error": f"Failed to fetch repositories: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)