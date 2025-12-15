import requests
import json
import base64
from django.conf import settings
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiTypes

from accounts.models import Tenant
from accounts.permissions import IsTenantOwner
from repositories.models import TenantCredential


@method_decorator(csrf_exempt, name='dispatch')
class GitHubOAuthCallbackView(APIView):
    permission_classes = []

    def get(self, request):
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        if error:
            return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?error=oauth_denied")
        
        if not code or not state:
            return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?error=invalid_callback")
        
        try:
            state_data = json.loads(base64.b64decode(state).decode())
            tenant_id = state_data.get('tenant_id')
            return_url = state_data.get('return_url', '/tenant-dashboard')
            
            if not tenant_id:
                return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?error=invalid_state")
            
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
            
            user_response = requests.get('https://api.github.com/user', headers={
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json'
            })
            
            if user_response.status_code != 200:
                return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?error=github_api_failed")
            
            github_user = user_response.json()
            
            orgs = []
            if 'read:org' in scope:
                orgs_response = requests.get('https://api.github.com/user/orgs', headers={
                    'Authorization': f'token {access_token}',
                    'Accept': 'application/vnd.github.v3+json'
                })
                if orgs_response.status_code == 200:
                    orgs = orgs_response.json()
            
            tenant = get_object_or_404(Tenant, id=tenant_id)
            
            existing_credential = TenantCredential.objects.filter(
                tenant=tenant,
                provider='github',
                github_account_id=str(github_user['id'])
            ).first()
            
            if existing_credential:
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
            
            return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?github_connected=true&credential_id={credential.id}")
            
        except Exception as e:
            print(f"GitHub OAuth error: {str(e)}")
            return redirect(f"{settings.FRONTEND_URL}/tenant-dashboard?error=oauth_processing_failed")

github_oauth_callback = GitHubOAuthCallbackView.as_view()


class GitHubCredentialActionsView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Revoke GitHub Credential",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Credentials"]
    )
    def post(self, request, tenant_id, credential_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        credential = get_object_or_404(TenantCredential, id=credential_id, tenant=tenant, provider='github')
        
        try:
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
            
            credential.is_active = False
            credential.save()
            
            return Response({"message": "GitHub credential revoked successfully"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": f"Failed to revoke credential: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Fetch GitHub Repositories",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Repositories"]
    )
    def get(self, request, tenant_id, credential_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        credential = get_object_or_404(TenantCredential, id=credential_id, tenant=tenant, provider='github')
        
        if not credential.is_active:
            return Response({"error": "Credential is not active"}, status=status.HTTP_400_BAD_REQUEST)
        
        access_token = credential.get_access_token()
        if not access_token:
            return Response({"error": "No access token available"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
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
            
            credential.last_used_at = timezone.now()
            credential.save(update_fields=['last_used_at'])
            
            return Response({
                'repositories': formatted_repos,
                'total_count': len(formatted_repos)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": f"Failed to fetch repositories: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

github_repositories = GitHubCredentialActionsView.as_view()
revoke_github_credential = GitHubCredentialActionsView.as_view()
