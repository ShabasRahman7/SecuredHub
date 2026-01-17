
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    MarkNotificationsReadSerializer
)

class NotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    @extend_schema(
        summary="List Notifications",
        parameters=[
            OpenApiParameter('is_read', OpenApiTypes.BOOL, description='Filter by read status'),
            OpenApiParameter('notification_type', OpenApiTypes.STR, description='Filter by notification type'),
            OpenApiParameter('page', OpenApiTypes.INT, description='Page number'),
            OpenApiParameter('page_size', OpenApiTypes.INT, description='Items per page (max 100)'),
        ],
        responses={200: NotificationListSerializer(many=True)},
        tags=["Notifications"]
    )
    def get(self, request):
        queryset = Notification.objects.filter(user=request.user)
        
        is_read_param = request.query_params.get('is_read')
        if is_read_param is not None:
            is_read = is_read_param.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_read=is_read)
        
        notification_type = request.query_params.get('notification_type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        serializer = NotificationListSerializer(paginated_queryset, many=True)
        
        return paginator.get_paginated_response(serializer.data)

class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Notification Details",
        responses={200: NotificationSerializer},
        tags=["Notifications"]
    )
    def get(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=request.user
            )
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MarkNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark Notifications as Read",
        request=MarkNotificationsReadSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["Notifications"]
    )
    def post(self, request):
        serializer = MarkNotificationsReadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notification_ids = serializer.validated_data['notification_ids']
        
        updated_count = Notification.objects.filter(
            id__in=notification_ids,
            user=request.user,
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'success': True,
            'marked_read': updated_count
        }, status=status.HTTP_200_OK)

class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark All Notifications as Read",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Notifications"]
    )
    def post(self, request):
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'success': True,
            'marked_read': updated_count
        }, status=status.HTTP_200_OK)

class ClearAllNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Clear All Notifications",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Notifications"]
    )
    def delete(self, request):
        deleted_count, _ = Notification.objects.filter(user=request.user).delete()
        
        return Response({
            'success': True,
            'deleted': deleted_count
        }, status=status.HTTP_200_OK)

class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Unread Count",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Notifications"]
    )
    def get(self, request):
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)

notification_list = NotificationListView.as_view()
notification_detail = NotificationDetailView.as_view()
mark_notifications_read = MarkNotificationsReadView.as_view()
mark_all_notifications_read = MarkAllNotificationsReadView.as_view()
clear_all_notifications = ClearAllNotificationsView.as_view()
unread_count = UnreadCountView.as_view()
