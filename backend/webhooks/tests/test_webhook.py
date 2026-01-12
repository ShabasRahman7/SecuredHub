import pytest
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from django.test import Client
from rest_framework import status

from webhooks.github_api import (
    generate_webhook_secret,
    parse_github_repo_info,
    verify_webhook_signature
)


class TestGitHubAPI:
    
    def test_generate_webhook_secret_length(self):
        secret = generate_webhook_secret()
        assert len(secret) == 64
    
    def test_generate_webhook_secret_unique(self):
        secret1 = generate_webhook_secret()
        secret2 = generate_webhook_secret()
        assert secret1 != secret2
    
    def test_parse_github_repo_info_https(self):
        url = 'https://github.com/owner/repo'
        result = parse_github_repo_info(url)
        assert result == ('owner', 'repo')
    
    def test_parse_github_repo_info_with_git_suffix(self):
        url = 'https://github.com/owner/repo.git'
        result = parse_github_repo_info(url)
        assert result == ('owner', 'repo')
    
    def test_parse_github_repo_info_invalid(self):
        url = 'https://gitlab.com/owner/repo'
        result = parse_github_repo_info(url)
        assert result is None
    
    def test_verify_webhook_signature_valid(self):
        secret = 'test-secret'
        payload = b'{"test": "data"}'
        signature = 'sha256=' + hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        assert verify_webhook_signature(payload, signature, secret) is True
    
    def test_verify_webhook_signature_invalid(self):
        secret = 'test-secret'
        payload = b'{"test": "data"}'
        
        assert verify_webhook_signature(payload, 'sha256=invalid', secret) is False
    
    def test_verify_webhook_signature_missing_prefix(self):
        secret = 'test-secret'
        payload = b'{"test": "data"}'
        
        assert verify_webhook_signature(payload, 'invalid', secret) is False


@pytest.mark.django_db
class TestWebhookReceiver:
    
    def test_ping_event_returns_pong(self, client):
        response = client.post(
            '/api/v1/webhooks/github/',
            data='{}',
            content_type='application/json',
            HTTP_X_GITHUB_EVENT='ping'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['message'] == 'pong'
    
    def test_missing_signature_rejected(self, client):
        response = client.post(
            '/api/v1/webhooks/github/',
            data=json.dumps({'repository': {'html_url': 'https://github.com/test/repo'}}),
            content_type='application/json',
            HTTP_X_GITHUB_EVENT='push'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_unknown_repo_returns_ok(self, client, repository):
        payload = json.dumps({
            'repository': {'html_url': 'https://github.com/unknown/repo'},
            'after': 'abc123'
        })
        signature = 'sha256=' + hmac.new(
            b'fake-secret',
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        response = client.post(
            '/api/v1/webhooks/github/',
            data=payload,
            content_type='application/json',
            HTTP_X_GITHUB_EVENT='push',
            HTTP_X_HUB_SIGNATURE_256=signature
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['message'] == 'repository not registered'
    
    def test_push_event_triggers_scan(self, client, repository):
        repository.webhook_secret = 'test-webhook-secret'
        repository.save()
        
        payload = json.dumps({
            'repository': {'html_url': repository.url},
            'after': 'newcommit123',
            'ref': 'refs/heads/main'
        })
        signature = 'sha256=' + hmac.new(
            repository.webhook_secret.encode('utf-8'),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        with patch('celery.current_app') as mock_celery:
            mock_celery.send_task = MagicMock()
            
            response = client.post(
                '/api/v1/webhooks/github/',
                data=payload,
                content_type='application/json',
                HTTP_X_GITHUB_EVENT='push',
                HTTP_X_HUB_SIGNATURE_256=signature
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'scan_id' in response.json()
    
    def test_duplicate_commit_skipped(self, client, repository):
        repository.webhook_secret = 'test-webhook-secret'
        repository.last_scanned_commit = 'existingcommit'
        repository.save()
        
        payload = json.dumps({
            'repository': {'html_url': repository.url},
            'after': 'existingcommit',
            'ref': 'refs/heads/main'
        })
        signature = 'sha256=' + hmac.new(
            repository.webhook_secret.encode('utf-8'),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        response = client.post(
            '/api/v1/webhooks/github/',
            data=payload,
            content_type='application/json',
            HTTP_X_GITHUB_EVENT='push',
            HTTP_X_HUB_SIGNATURE_256=signature
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['message'] == 'commit already scanned'
