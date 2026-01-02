"""Views for scan API endpoints"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from repositories.models import Repository
from .models import Scan, ScanFinding  
from .serializers import ScanSerializer, ScanDetailSerializer, ScanFindingSerializer
from accounts.permissions import IsTenantMember, IsTenantOwner

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTenantMember])
def trigger_scan(request, repo_id):
    # getting user's tenant
    if not hasattr(request.user, 'tenant_membership') or not request.user.tenant_membership:
        return Response(
            {'error': 'User is not associated with any tenant'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    user_tenant = request.user.tenant_membership.tenant
    
    # getting repository (ensures user has access via IsTenantMember)
    repo = get_object_or_404(
        Repository.objects.select_related('tenant'),
        id=repo_id,
        tenant=user_tenant
    )
    
    # checking if there's already a queued or running scan for this repo
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
    
    # checking if this repo's latest commit was already scanned
    # this prevents wasting time cloning the repo in Celery
    if repo.last_scanned_commit:
        # checking if the latest commit on the repo is the same
        # note: We can't know the latest commit without cloning
        # but we can check if there was a recent completed scan
        recent_scan = Scan.objects.filter(
            repository=repo,
            status='completed',
            commit_hash=repo.last_scanned_commit
        ).order_by('-completed_at').first()
        
        if recent_scan:
            # returning the existing scan instead of creating a new one
            return Response(
                {
                    'message': 'Repository was already scanned with this commit',
                    'scan': ScanSerializer(recent_scan).data,
                    'note': 'Delete existing scan to force re-scan'
                },
                status=status.HTTP_200_OK
            )
    
    # creating scan record
    scan = Scan.objects.create(
        repository=repo,
        triggered_by=request.user,
        status='queued'
    )
    
    # queueing Celery task (using send_task to avoid importing from separate container)
    try:
        from celery import current_app
        # sending task by name (scanner worker will pick it up)
        current_app.send_task(
            'tasks.scan_repository_task',
            args=[repo.id, scan.id],
            queue='celery'
        )
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
    user_tenant = request.user.tenant_membership.tenant if hasattr(request.user, 'tenant_membership') else None
    
    scan = get_object_or_404(
        Scan.objects.select_related('repository', 'repository__tenant'),
        id=scan_id,
        repository__tenant=user_tenant
    )
    
    # don't allow deletion of running scans
    if scan.status in ['queued', 'running']:
        return Response(
            {'error': 'Cannot delete a scan that is currently queued or running'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    repository = scan.repository
    deleted_commit = scan.commit_hash
    
    # deleting the scan (cascade will delete findings)
    scan.delete()
    
    # updating repository's last_scanned_commit if we deleted the last completed scan
    if deleted_commit and repository.last_scanned_commit == deleted_commit:
        # finding the most recent completed scan for this repo (if any)
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
