from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiTypes
from celery import current_app

from accounts.models import Tenant
from accounts.permissions import IsTenantMember
from repositories.models import Repository
from .models import Scan
from .serializers import ScanSerializer, ScanFindingSerializer


class TriggerScanView(APIView):
    permission_classes = [IsAuthenticated, IsTenantMember]

    @extend_schema(
        summary="Trigger Scan",
        request=OpenApiTypes.OBJECT,
        responses={201: ScanSerializer},
        tags=["Scans"]
    )
    def post(self, request, repo_id):
        repo = get_object_or_404(Repository, id=repo_id)
        self.check_object_permissions(request, repo.tenant)
        
        # Create scan record
        scan = Scan.objects.create(
            repository=repo,
            triggered_by=request.user,
            status="queued",
            branch=repo.default_branch
        )
        
        # Queue the scan task (calls standalone worker)
        task = current_app.send_task("scans.tasks.run_security_scan", args=[scan.id])
        
        # Serialize and return
        serializer = ScanSerializer(scan)
        return Response({
            **serializer.data,
            'task_id': task.id
        }, status=status.HTTP_201_CREATED)


class ListScansView(APIView):
    permission_classes = [IsAuthenticated, IsTenantMember]

    @extend_schema(
        summary="List Scans",
        responses={200: ScanSerializer(many=True)},
        tags=["Scans"]
    )
    def get(self, request, repo_id):
        repo = get_object_or_404(Repository, id=repo_id)
        self.check_object_permissions(request, repo.tenant)
        
        scans = repo.scans.order_by("-created_at")
        return Response(ScanSerializer(scans, many=True).data, status=status.HTTP_200_OK)



trigger_scan = TriggerScanView.as_view()
list_scans = ListScansView.as_view()
