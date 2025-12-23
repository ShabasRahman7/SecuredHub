"""
WebSocket consumer for compliance evaluation updates.
"""
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from compliance.models import ComplianceEvaluation


class EvaluationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time evaluation progress updates."""
    
    async def connect(self):
        self.evaluation_id = self.scope['url_route']['kwargs']['evaluation_id']
        self.group_name = f'evaluation_{self.evaluation_id}'
        self.user = self.scope.get('user')

        # Auth check
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        evaluation = await self.get_evaluation()
        if not evaluation:
            await self.close()
            return

        has_permission = await self.check_permission(evaluation)
        if not has_permission:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send current status
        await self.send(text_data=json.dumps({
            'type': 'evaluation_status',
            'evaluation_id': self.evaluation_id,
            'status': evaluation.status,
            'message': f'Connected to evaluation {self.evaluation_id}'
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'evaluation_id': self.evaluation_id
                }))
        except json.JSONDecodeError:
            return

    async def evaluation_update(self, event):
        """Handle evaluation update events from Celery worker."""
        await self.send(text_data=json.dumps({
            'type': 'evaluation_update',
            'evaluation_id': event.get('evaluation_id'),
            'status': event.get('status'),
            'message': event.get('message', ''),
            'progress': event.get('progress'),
            'score': event.get('score'),
            'passed_count': event.get('passed_count'),
            'failed_count': event.get('failed_count'),
            'total_rules': event.get('total_rules'),
        }))

    @database_sync_to_async
    def get_evaluation(self):
        try:
            return ComplianceEvaluation.objects.select_related(
                'repository__tenant'
            ).get(id=self.evaluation_id)
        except ComplianceEvaluation.DoesNotExist:
            return None

    @database_sync_to_async
    def check_permission(self, evaluation):
        if not self.user or not self.user.is_authenticated:
            return False
        if self.user.is_staff:
            return True

        try:
            from accounts.models import TenantMember
            return TenantMember.objects.filter(
                user=self.user,
                tenant=evaluation.repository.tenant,
                deleted_at__isnull=True
            ).exists()
        except Exception:
            return False
