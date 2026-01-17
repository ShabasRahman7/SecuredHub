
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from repositories.models import Repository
from .models import Scan, ScanFinding  
from .serializers import ScanSerializer, ScanDetailSerializer, ScanFindingSerializer
from .utils import get_remote_latest_commit
from accounts.permissions import IsTenantMember, IsTenantOwner

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTenantMember])
def trigger_scan(request, repo_id):

    if not hasattr(request.user, 'tenant_membership') or not request.user.tenant_membership:
        return Response(
            {'error': 'User is not associated with any tenant'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    user_tenant = request.user.tenant_membership.tenant
    

    repo = get_object_or_404(
        Repository.objects.select_related('tenant', 'credential'),
        id=repo_id,
        tenant=user_tenant
    )
    

    existing_scan = Scan.objects.filter(
        repository=repo,
        status__in=['queued', 'running']
    ).first()
    
    if existing_scan:
        return Response(
            {
                'error': 'A scan is already in progress for this repository',
                'scan_id': existing_scan.id,
                'status': existing_scan.status
            },
            status=status.HTTP_409_CONFLICT
        )
    

    access_token = repo.credential.get_access_token() if repo.credential else None
    remote_latest_commit = get_remote_latest_commit(repo.url, repo.default_branch or 'HEAD', access_token)
    
    repo.refresh_from_db()
    

    

    if remote_latest_commit and remote_latest_commit == repo.last_scanned_commit:
        recent_scan = Scan.objects.filter(
            repository=repo,
            status='completed',
            commit_hash=remote_latest_commit
        ).order_by('-completed_at').first()
        
        if recent_scan:

            return Response(
                {
                    'message': 'Repository was already scanned with the latest commit',
                    'scan': ScanSerializer(recent_scan).data,
                    'commit': remote_latest_commit[:7],
                    'note': 'Push new commits or delete existing scan to trigger a new scan'
                },
                status=status.HTTP_200_OK
            )
    

    scan = Scan.objects.create(
        repository=repo,
        triggered_by=request.user,
        status='queued'
    )
    
    # submit K8s scan job
    try:
        from scans.k8s_runner import submit_scan_job
        result = submit_scan_job(
            scan_id=scan.id,
            repo_url=repo.url,
            commit_sha=remote_latest_commit or 'HEAD'
        )
        if not result.get('success'):
            raise Exception(result.get('error', 'K8s job submission failed'))
    except Exception as e:
        scan.status = 'failed'
        scan.error_message = f"Failed to queue scan: {str(e)}"
        scan.save()
        return Response(
            {'error': f'Failed to queue scan task: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response(
        ScanSerializer(scan).data,
        status=status.HTTP_201_CREATED
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTenantMember])
def get_scan_detail(request, scan_id):
    user_tenant = request.user.tenant_membership.tenant if hasattr(request.user, 'tenant_membership') else None
    
    scan = get_object_or_404(
        Scan.objects.select_related('repository', 'repository__tenant'),
        id=scan_id,
        repository__tenant=user_tenant
    )
    
    return Response(ScanDetailSerializer(scan).data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTenantMember])
def get_scan_findings(request, scan_id):
    user_tenant = request.user.tenant_membership.tenant if hasattr(request.user, 'tenant_membership') else None
    
    scan = get_object_or_404(
        Scan.objects.select_related('repository', 'repository__tenant'),
        id=scan_id,
        repository__tenant=user_tenant
    )
    
    findings = scan.findings.all()
    
    # filtering by severity
    severity = request.query_params.get('severity')
    if severity:
        findings = findings.filter(severity=severity)
    
    # filtering by tool
    tool = request.query_params.get('tool')
    if tool:
        findings = findings.filter(tool=tool)
    
    return Response(ScanFindingSerializer(findings, many=True).data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTenantMember])
def get_repository_scans(request, repo_id):
    user_tenant = request.user.tenant_membership.tenant if hasattr(request.user, 'tenant_membership') else None
    
    repo = get_object_or_404(
        Repository.objects.select_related('tenant'),
        id=repo_id,
        tenant=user_tenant
    )
    
    scans = Scan.objects.filter(repository=repo).order_by('-created_at')
    
    return Response(ScanSerializer(scans, many=True).data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsTenantOwner])
def delete_scan(request, scan_id):
    from django.utils import timezone
    from datetime import timedelta
    
    user_tenant = request.user.tenant_membership.tenant if hasattr(request.user, 'tenant_membership') else None
    
    scan = get_object_or_404(
        Scan.objects.select_related('repository', 'repository__tenant'),
        id=scan_id,
        repository__tenant=user_tenant
    )
    
    force = request.query_params.get('force', 'false').lower() == 'true'
    
    # only block deletion of actively running scans (not queued or failed)
    if scan.status == 'running' and not force:
        # check if scan is stuck (running for more than 10 minutes without updates)
        if scan.started_at:
            stuck_threshold = timezone.now() - timedelta(minutes=10)
            if scan.started_at < stuck_threshold:
                # auto-mark as failed since it's stuck
                scan.status = 'failed'
                scan.error_message = 'Scan timed out (stuck for over 10 minutes)'
                scan.save()
            else:
                return Response(
                    {'error': 'Cannot delete a scan that is currently running. Wait for completion or use ?force=true'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': 'Cannot delete a scan that is currently running'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    repository = scan.repository
    deleted_commit = scan.commit_hash
    
    scan.delete()
    
    # update repository's last_scanned_commit if we deleted the last completed scan
    if deleted_commit and repository.last_scanned_commit == deleted_commit:
        latest_scan = Scan.objects.filter(
            repository=repository,
            status='completed',
            commit_hash__isnull=False
        ).order_by('-completed_at').first()
        
        if latest_scan:
            repository.last_scanned_commit = latest_scan.commit_hash
        else:
            repository.last_scanned_commit = None
        
        repository.save()
    
    return Response(
        {'message': 'Scan deleted successfully'},
        status=status.HTTP_200_OK
    )
