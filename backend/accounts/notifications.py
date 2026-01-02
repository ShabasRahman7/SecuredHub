# realtime WebSocket notifications for different user roles
import json
import logging
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    # websocket handler for user notifications
    
    async def connect(self):
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # each user gets their own notification group
        self.group_name = f'notifications_user_{self.user.id}'
        
        # also add to role-based groups for broadcasts
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        # admin users join the admin broadcast group
        if self.user.is_staff or self.user.is_superuser:
            await self.channel_layer.group_add('notifications_admins', self.channel_name)
        
        await self.accept()
        
        # sending connection confirmation
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
        # handling ping/pong for connection keepalive
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
        # broadcasting to this WebSocket connection
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification_type': event.get('notification_type'),
            'title': event.get('title', ''),
            'message': event.get('message', ''),
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp'),
        }))

def send_notification(user_id: int, notification_type: str, title: str, message: str, data: dict = None):
    # sending notification to specific user via WebSocket and save to database
    from django.utils import timezone
    from notifications.models import Notification
    from .models import User
    
    # saving notification to database for persistence
    try:
        user = User.objects.get(id=user_id)
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {}
        )
        logger.info(f"Notification saved to database for user {user_id}: {notification_type}")
    except User.DoesNotExist:
        logger.error(f"Cannot save notification: User {user_id} does not exist")
        return
    except Exception as e:
        logger.error(f"Failed to save notification to database for user {user_id}: {e}")
        # continue to try WebSocket even if database save fails
    
    # sending real-time notification via WebSocket
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("Channel layer not available, skipping realtime notification")
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
        logger.info(f"Realtime notification sent to user {user_id}: {notification_type}")
    except Exception as e:
        logger.error(f"Failed to send realtime notification to user {user_id}: {e}")

def notify_admins(notification_type: str, title: str, message: str, data: dict = None):
    # broadcasting to all admin users
    from django.utils import timezone
    from notifications.models import Notification
    from .models import User
    
    # saving notification to database for all admin users
    try:
        admin_users = User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True)
        admin_users = admin_users.distinct()
        
        notifications_to_create = [
            Notification(
                user=admin_user,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data or {}
            )
            for admin_user in admin_users
        ]
        
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)
            logger.info(f"Admin notification saved to database for {len(notifications_to_create)} admins: {notification_type}")
    except Exception as e:
        logger.error(f"Failed to save admin notification to database: {e}")
    
    # sending real-time notification via WebSocket
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("Channel layer not available, skipping realtime admin notification")
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
        logger.info(f"Realtime admin notification sent: {notification_type}")
    except Exception as e:
       logger.error(f"Failed to send realtime admin notification: {e}")

def notify_tenant_owners(tenant_id: int, notification_type: str, title: str, message: str, data: dict = None):
    # sending notification to all owners of a tenant
    from .models import TenantMember
    
    # getting all owners of this tenant
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
