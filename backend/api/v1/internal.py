# aPI views
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings

from scans.models import Scan, ScanFinding
from scans.serializers import ScanDetailSerializer

def _verify_internal_token(request):
    token = request.headers.get('X-Internal-Token')
    expected_token = getattr(settings, 'INTERNAL_SERVICE_TOKEN', None)
    
    if not expected_token or token != expected_token:
        return False
    return True

@api_view(['POST'])
@permission_classes([AllowAny])  # Auth via internal token
def update_scan_status(request, scan_id):
    if not _verify_internal_token(request):
        return Response(
            {'error': 'Invalid internal service token'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    scan = get_object_or_404(Scan, id=scan_id)
    
    scan_status = request.data.get('status')
    if scan_status:
        scan.status = scan_status
    
    if request.data.get('error_message'):
        scan.error_message = request.data['error_message']
    
    if request.data.get('commit_hash'):
        scan.commit_hash = request.data['commit_hash']
    
    if request.data.get('started_at'):
        from django.utils.dateparse import parse_datetime
        scan.started_at = parse_datetime(request.data['started_at'])
    
    if request.data.get('completed_at'):
        from django.utils.dateparse import parse_datetime
        scan.completed_at = parse_datetime(request.data['completed_at'])
    
    scan.save()
    
    # broadcasting scan status update to WebSocket clients
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'scan_{scan_id}',
            {
                'type': 'scan_update',
                'scan_id': scan_id,
                'status': scan.status,
                'message': request.data.get('message', f'Scan {scan.status}'),
                'progress': request.data.get('progress', 0),
                'findings_count': scan.findings.count() if scan.status == 'completed' else 0
            }
        )
    except Exception as e:
        # continuing even if WebSocket broadcast fails
        print(f"WebSocket broadcast failed: {e}")
    
    return Response({'status': 'updated'})

@api_view(['POST'])
@permission_classes([AllowAny])  # Auth via internal token
def submit_scan_findings(request, scan_id):
    if not _verify_internal_token(request):
        return Response(
            {'error': 'Invalid internal service token'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    scan = get_object_or_404(Scan.objects.select_related('repository'), id=scan_id)
    
    findings_data = request.data.get('findings', [])
    
    # bulk create findings
    finding_objects = []
    for finding_data in findings_data:
        finding = ScanFinding(
            scan=scan,
            tool=finding_data.get('tool', 'unknown'),
            rule_id=finding_data.get('rule_id', ''),
            title=finding_data.get('title', ''),
            description=finding_data.get('description', ''),
            severity=finding_data.get('severity', 'medium'),
            file_path=finding_data.get('file_path', ''),
            line_number=finding_data.get('line_number'),
            raw_output=finding_data.get('raw_output', {})
        )
        finding_objects.append(finding)
    
    ScanFinding.objects.bulk_create(finding_objects)
    
    # updating repository's last scanned commit if requested
    if request.data.get('update_repo_commit') and request.data.get('commit_hash'):
        scan.repository.last_scanned_commit = request.data['commit_hash']
        scan.repository.save()
    
    return Response({
        'status': 'created',
        'findings_count': len(finding_objects)
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([AllowAny])  # Auth via internal token
def get_repository_info(request, repo_id):
    if not _verify_internal_token(request):
        return Response(
            {'error': 'Invalid internal service token'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from repositories.models import Repository
    repo = get_object_or_404(Repository.objects.select_related('credential'), id=repo_id)
    
    # getting access token if available
    access_token = None
    if repo.credential:
        access_token = repo.credential.get_access_token()
    
    return Response({
        'id': repo.id,
        'name': repo.name,
        'url': repo.url,
        'default_branch': repo.default_branch,
        'last_scanned_commit': repo.last_scanned_commit,
        'access_token': access_token  # Only sent to internal service
    })
