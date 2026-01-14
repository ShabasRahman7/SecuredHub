from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer


class AuditLogPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def list_audit_logs(request):
    event_type = request.query_params.get('event_type')
    tenant_id = request.query_params.get('tenant_id')
    actor_email = request.query_params.get('actor_email')
    
    queryset = AuditLog.objects.all()
    
    if event_type:
        queryset = queryset.filter(event_type=event_type)
    if tenant_id:
        queryset = queryset.filter(tenant_id=tenant_id)
    if actor_email:
        queryset = queryset.filter(actor_email__icontains=actor_email)
    
    paginator = AuditLogPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = AuditLogSerializer(page, many=True)
    
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_audit_stats(request):
    last_24h = timezone.now() - timedelta(hours=24)
    last_7d = timezone.now() - timedelta(days=7)
    
    stats = {
        'total': AuditLog.objects.count(),
        'last_24h': AuditLog.objects.filter(created_at__gte=last_24h).count(),
        'last_7d': AuditLog.objects.filter(created_at__gte=last_7d).count(),
        'by_type': list(
            AuditLog.objects.values('event_type')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
    }
    
    return Response(stats)
