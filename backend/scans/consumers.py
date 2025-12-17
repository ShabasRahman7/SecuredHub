import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Scan

SKIP_AUTH = False  # Set True only for wscat testing


class ScanConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.scan_id = self.scope['url_route']['kwargs']['scan_id']
        self.group_name = f'scan_{self.scan_id}'
        self.user = self.scope.get('user')

        if not SKIP_AUTH:
            if not self.user or not self.user.is_authenticated:
                await self.close()
                return

        scan = await self.get_scan()
        if not scan:
            await self.close()
            return

        if not SKIP_AUTH:
            has_permission = await self.check_permission(scan)
            if not has_permission:
                await self.close()
                return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            'type': 'scan_status',
            'scan_id': self.scan_id,
            'status': scan.status,
            'message': f'Connected to scan {self.scan_id}'
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'scan_id': self.scan_id
                }))
        except json.JSONDecodeError:
            return

    async def scan_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'scan_update',
            'scan_id': event['scan_id'],
            'status': event['status'],
            'message': event.get('message', ''),
            'progress': event.get('progress'),
            'findings_count': event.get('findings_count', 0),
        }))

    @database_sync_to_async
    def get_scan(self):
        try:
            return Scan.objects.select_related('repository__tenant').get(id=self.scan_id)
        except Scan.DoesNotExist:
            return None

    @database_sync_to_async
    def check_permission(self, scan):
        if not self.user or not self.user.is_authenticated:
            return False
        if self.user.is_staff:
            return True

        try:
            from accounts.models import TenantMember
            return TenantMember.objects.filter(
                user=self.user,
                tenant=scan.repository.tenant,
                deleted_at__isnull=True
            ).exists()
        except Exception:
            return False
