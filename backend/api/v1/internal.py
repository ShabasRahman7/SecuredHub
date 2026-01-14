
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Count

from scans.models import Scan, ScanFinding
from scans.serializers import ScanDetailSerializer
from scans.sns_publisher import SNSPublisher

def _verify_internal_token(request):
    token = request.headers.get('X-Internal-Token')
    expected_token = getattr(settings, 'INTERNAL_SERVICE_TOKEN', None)
    
    if not expected_token or token != expected_token:
        return False
    return True

@api_view(['POST'])
@permission_classes([AllowAny])
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
    
    if 'progress' in request.data:
        scan.progress = request.data['progress']
    
    if request.data.get('message'):
        scan.progress_message = request.data['message']
    
    scan.save()
    

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
        print(f"WebSocket broadcast failed: {e}")
    
    
    if scan_status == 'completed':
        try:
            repo = scan.repository
            tenant = repo.tenant
            
            severity_counts = scan.findings.values('severity').annotate(count=Count('id'))
            severity_breakdown = {item['severity']: item['count'] for item in severity_counts}
            
            notification_targets = []
            for member in tenant.members.filter(deleted_at__isnull=True).select_related('user'):
                notification_targets.append({
                    'email': member.user.email,
                    'role': member.role
                })
            
            sns = SNSPublisher()
            sns.publish_scan_completed({
                'scan_id': scan.id,
                'repo_id': repo.id,
                'repo_name': repo.name,
                'tenant_id': tenant.id,
                'tenant_name': tenant.name,
                'triggered_by': scan.triggered_by if hasattr(scan, 'triggered_by') else 'manual',
                'findings_count': scan.findings.count(),
                'severity_breakdown': severity_breakdown,
                'commit_hash': scan.commit_hash,
                'scan_url': f"{settings.FRONTEND_URL}/scans/{scan.id}" if hasattr(settings, 'FRONTEND_URL') else None,
                'notification_targets': notification_targets
            })
        except Exception as e:
            print(f"SNS publish failed: {e}")
    
    return Response({'status': 'updated'})

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_scan_findings(request, scan_id):
    if not _verify_internal_token(request):
        return Response(
            {'error': 'Invalid internal service token'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    scan = get_object_or_404(Scan.objects.select_related('repository'), id=scan_id)
    
    findings_data = request.data.get('findings', [])
    

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
    

    if request.data.get('update_repo_commit') and request.data.get('commit_hash'):
        scan.repository.last_scanned_commit = request.data['commit_hash']
        scan.repository.save()
    
    return Response({
        'status': 'created',
        'findings_count': len(finding_objects)
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_repository_info(request, repo_id):
    if not _verify_internal_token(request):
        return Response(
            {'error': 'Invalid internal service token'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from repositories.models import Repository
    repo = get_object_or_404(Repository.objects.select_related('credential'), id=repo_id)
    

    access_token = None
    if repo.credential:
        access_token = repo.credential.get_access_token()
    
    return Response({
        'id': repo.id,
        'name': repo.name,
        'url': repo.url,
        'default_branch': repo.default_branch,
        'last_scanned_commit': repo.last_scanned_commit,
        'access_token': access_token
    })
