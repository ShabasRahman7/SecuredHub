from rest_framework import serializers
from audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            'id', 'event_type', 'actor_id', 'actor_email',
            'target_type', 'target_id', 'target_name',
            'tenant_id', 'tenant_name', 'ip_address',
            'metadata', 'created_at'
        ]
