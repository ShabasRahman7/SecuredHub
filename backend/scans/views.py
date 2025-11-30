from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import Tenant, TenantMember
from repositories.models import Repository
from .models import Scan
from .serializers import ScanSerializer, ScanFindingSerializer
from datetime import datetime

@extend_schema(
    summary="Trigger Scan",
    description="Trigger a new security scan for a repository.",
    request=OpenApiTypes.OBJECT,
    responses={201: ScanSerializer},
    tags=["Scans"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_scan(request, repo_id):
    user = request.user

    # Verify repo exists
    try:
        repo = Repository.objects.get(id=repo_id)
    except Repository.DoesNotExist:
        return Response({"detail": "Repository not found"}, status=404)

    # Verify user belongs to the org
    is_member = TenantMember.objects.filter(
        user=user,
        tenant=repo.tenant
    ).exists()

    if not is_member:
        return Response({"detail": "Not allowed"}, status=403)

    # Create new Scan in queued state
    scan = Scan.objects.create(
        repository=repo,
        triggered_by=user,
        status="queued",
        branch=repo.default_branch
    )

    # This will be executed in Week 2
    # async_task_scan.delay(scan.id)

    return Response(ScanSerializer(scan).data, status=201)

@extend_schema(
    summary="List Scans",
    description="List all scans for a repository.",
    responses={200: ScanSerializer(many=True)},
    tags=["Scans"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_scans(request, repo_id):
    user = request.user

    try:
        repo = Repository.objects.get(id=repo_id)
    except Repository.DoesNotExist:
        return Response({"detail": "Repo not found"}, status=404)

    is_member = TenantMember.objects.filter(
        user=user,
        tenant=repo.tenant
    ).exists()

    if not is_member:
        return Response({"detail": "Not allowed"}, status=403)

    scans = repo.scans.order_by("-created_at")
    return Response(ScanSerializer(scans, many=True).data)

@extend_schema(
    summary="Scan Details",
    description="Get detailed results of a scan including findings.",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Scans"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_details(request, scan_id):
    user = request.user

    try:
        scan = Scan.objects.get(id=scan_id)
    except Scan.DoesNotExist:
        return Response({"detail": "Scan not found"}, status=404)

    if not TenantMember.objects.filter(
        user=user, tenant=scan.repository.tenant
    ).exists():
        return Response({"detail": "Not allowed"}, status=403)

    data = {
        "scan": ScanSerializer(scan).data,
        "findings": ScanFindingSerializer(scan.findings.all(), many=True).data
    }

    return Response(data)
