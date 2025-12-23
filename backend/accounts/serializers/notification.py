"""
Notification serializers.
"""
from rest_framework import serializers
from accounts.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'data',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['id', 'notification_type', 'title', 'message', 'data', 'created_at']


class NotificationListSerializer(serializers.ModelSerializer):
    """Compact serializer for notification list."""
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'created_at',
        ]
