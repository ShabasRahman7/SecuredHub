import json
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

from repositories.models import Repository
from scans.models import Scan
from .github_api import verify_webhook_signature


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def github_webhook_receiver(request):
    event_type = request.headers.get('X-GitHub-Event')
    
    if event_type == 'ping':
        return Response({'message': 'pong'}, status=status.HTTP_200_OK)
    
    if event_type != 'push':
        return Response({'message': 'event ignored'}, status=status.HTTP_200_OK)
    
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        return Response({'error': 'missing signature'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return Response({'error': 'invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
    
    repo_url = payload.get('repository', {}).get('html_url')
    if not repo_url:
        return Response({'error': 'missing repository url'}, status=status.HTTP_400_BAD_REQUEST)
    
    repository = Repository.objects.filter(
        url__icontains=repo_url.replace('https://github.com/', ''),
        is_active=True
    ).first()
    
    if not repository:
        return Response({'message': 'repository not registered'}, status=status.HTTP_200_OK)
    
    if not repository.webhook_secret:
        return Response({'error': 'webhook not configured'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not verify_webhook_signature(request.body, signature, repository.webhook_secret):
        return Response({'error': 'invalid signature'}, status=status.HTTP_403_FORBIDDEN)
    
    commit_hash = payload.get('after')
    if not commit_hash or commit_hash == '0000000000000000000000000000000000000000':
        return Response({'message': 'no commit to scan'}, status=status.HTTP_200_OK)
    
    if repository.last_scanned_commit == commit_hash:
        return Response({'message': 'commit already scanned'}, status=status.HTTP_200_OK)
    
    existing_scan = Scan.objects.filter(
        repository=repository,
        status__in=['queued', 'running']
    ).first()
    
    if existing_scan:
        return Response({
            'message': 'scan already in progress',
            'scan_id': existing_scan.id
        }, status=status.HTTP_200_OK)
    
    scan = Scan.objects.create(
        repository=repository,
        triggered_by=None,
        status='queued',
        branch=payload.get('ref', '').replace('refs/heads/', '')
    )
    
    try:
        from celery import current_app
        current_app.send_task(
            'tasks.scan_repository_task',
            args=[repository.id, scan.id],
            queue='celery'
        )
    except Exception as e:
        scan.status = 'failed'
        scan.error_message = f"Failed to queue scan: {str(e)}"
        scan.save()
        return Response({'error': 'failed to queue scan'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'message': 'scan triggered',
        'scan_id': scan.id,
        'commit': commit_hash[:7]
    }, status=status.HTTP_201_CREATED)
