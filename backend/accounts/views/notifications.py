"""
Notification API views.

Provides endpoints for managing user notifications:
- List notifications (auto-marks as read)
- Delete notifications
- Clear all notifications
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from accounts.models import Notification
from accounts.serializers.notification import NotificationSerializer, NotificationListSerializer


class NotificationListView(APIView):
    """
    GET /auth/notifications/
    List all notifications for the authenticated user.
    
    Auto-marks all returned notifications as read (since user has viewed them).
    
    Query params:
        - limit: int (default: 50, max: 100)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        limit = min(int(request.query_params.get('limit', 50)), 100)
        
        # Get notifications
        notifications = Notification.objects.filter(user=request.user)[:limit]
        
        # Get IDs of unread notifications before we mark them
        notification_ids = list(notifications.values_list('id', flat=True))
        
        serializer = NotificationListSerializer(notifications, many=True)
        
        # Auto-mark as read since user is viewing them
        Notification.objects.filter(
            user=request.user,
            id__in=notification_ids,
            is_read=False
        ).update(is_read=True)
        
        # Return 0 unread count since we just marked them all read
        return Response({
            'notifications': serializer.data,
            'unread_count': 0,
        })


class NotificationDetailView(APIView):
    """
    GET /auth/notifications/{id}/
    Get a single notification (auto-marks as read).
    
    DELETE /auth/notifications/{id}/
    Delete a notification.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            user=request.user
        )
        # Auto-mark as read
        notification.mark_as_read()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)
    
    def delete(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            user=request.user
        )
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClearAllNotificationsView(APIView):
    """
    DELETE /auth/notifications/clear-all/
    Delete all notifications for the user.
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        count, _ = Notification.objects.filter(user=request.user).delete()
        
        return Response({
            'deleted': count,
            'message': f'{count} notification(s) deleted'
        })


class UnreadCountView(APIView):
    """
    GET /auth/notifications/unread-count/
    Get the count of unread notifications.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({'unread_count': count})
