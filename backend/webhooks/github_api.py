import hmac
import hashlib
import secrets
import requests
import re
from typing import Optional, Tuple
from django.conf import settings


def generate_webhook_secret() -> str:
    return secrets.token_hex(32)


def parse_github_repo_info(repo_url: str) -> Optional[Tuple[str, str]]:
    patterns = [
        r'github\.com[:/]([^/]+)/([^/\.]+)',
        r'github\.com/([^/]+)/([^/]+?)(?:\.git)?$',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, repo_url)
        if match:
            repo_name = match.group(2)
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            return match.group(1), repo_name
    
    return None


def create_webhook(repo_url: str, access_token: str, webhook_url: str, secret: str) -> Optional[str]:
    repo_info = parse_github_repo_info(repo_url)
    if not repo_info:
        return None
    
    owner, repo = repo_info
    
    api_url = f'https://api.github.com/repos/{owner}/{repo}/hooks'
    
    payload = {
        'name': 'web',
        'active': True,
        'events': ['push'],
        'config': {
            'url': webhook_url,
            'content_type': 'json',
            'secret': secret,
            'insecure_ssl': '0'
        }
    }
    
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 201:
            return str(response.json().get('id'))
        
        return None
        
    except requests.exceptions.RequestException:
        return None


def delete_webhook(repo_url: str, access_token: str, webhook_id: str) -> bool:
    repo_info = parse_github_repo_info(repo_url)
    if not repo_info:
        return False
    
    owner, repo = repo_info
    
    api_url = f'https://api.github.com/repos/{owner}/{repo}/hooks/{webhook_id}'
    
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.delete(api_url, headers=headers, timeout=30)
        return response.status_code in [204, 404]
        
    except requests.exceptions.RequestException:
        return False


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    if not signature or not signature.startswith('sha256='):
        return False
    
    expected_signature = 'sha256=' + hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
