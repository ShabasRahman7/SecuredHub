"""
Real-time notification system using Django Channels.

Provides WebSocket-based notifications for all user types:
- Admin: Access requests, new tenants
- Tenant Owner: Developer joined, scan completed
- Developer: Repository assigned/unassigned
"""
import json
import logging
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


# ============================================================================
# WebSocket Consumer
# ============================================================================

class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for user-specific notifications.
    Connect to: ws://<host>/ws/notifications/?token=<JWT>
    """
    
    async def connect(self):
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Each user gets their own notification group
        self.group_name = f'notifications_user_{self.user.id}'
        
        # Also add to role-based groups for broadcasts
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        # Admin users join the admin broadcast group
        if self.user.is_staff or self.user.is_superuser:
            await self.channel_layer.group_add('notifications_admins', self.channel_name)
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to notification service',
            'user_id': self.user.id,
        }))
    
    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        
        if hasattr(self, 'user') and self.user and (self.user.is_staff or self.user.is_superuser):
            await self.channel_layer.group_discard('notifications_admins', self.channel_name)
    
    async def receive(self, text_data):
        """Handle incoming messages (ping/pong for keepalive)."""
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
        except json.JSONDecodeError:
            pass
    
    async def notification(self, event):
        """
        Handler for 'notification' type messages from channel layer.
        This method is called when send_notification() broadcasts to this group.
        """
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification_type': event.get('notification_type'),
            'title': event.get('title', ''),
            'message': event.get('message', ''),
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp'),
        }))


# ============================================================================
# Notification Helper Functions
# ============================================================================

def send_notification(user_id: int, notification_type: str, title: str, message: str, data: dict = None):
    """
    Send a notification to a specific user.
    
    Args:
        user_id: Target user's ID
        notification_type: Type of notification (e.g., 'repo_assigned', 'member_joined')
        title: Notification title
        message: Notification message
        data: Additional data payload
    """
    from django.utils import timezone
    
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("Channel layer not available, skipping notification")
        return
    
    group_name = f'notifications_user_{user_id}'
    
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notification',
                'notification_type': notification_type,
                'title': title,
                'message': message,
                'data': data or {},
                'timestamp': timezone.now().isoformat(),
            }
        )
        logger.info(f"Notification sent to user {user_id}: {notification_type}")
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}")


def notify_admins(notification_type: str, title: str, message: str, data: dict = None):
    """
    Broadcast notification to all admin users.
    
    Args:
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        data: Additional data payload
    """
    from django.utils import timezone
    
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("Channel layer not available, skipping admin notification")
        return
    
    try:
        async_to_sync(channel_layer.group_send)(
            'notifications_admins',
            {
                'type': 'notification',
                'notification_type': notification_type,
                'title': title,
                'message': message,
                'data': data or {},
                'timestamp': timezone.now().isoformat(),
            }
        )
        logger.info(f"Admin notification sent: {notification_type}")
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")


def notify_tenant_owners(tenant_id: int, notification_type: str, title: str, message: str, data: dict = None):
    """
    Send notification to all owners of a specific tenant.
    
    Args:
        tenant_id: Target tenant's ID
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        data: Additional data payload
    """
    from .models import TenantMember
    
    # Get all owners of this tenant
    owners = TenantMember.objects.filter(
        tenant_id=tenant_id,
        role=TenantMember.ROLE_OWNER,
        deleted_at__isnull=True
    ).select_related('user')
    
    for member in owners:
        send_notification(
            user_id=member.user.id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data
        )
