"""
Serializers for audit logging models.
"""
from rest_framework import serializers
from .models import AuditLog, EvaluationEvidence


class EvaluationEvidenceSerializer(serializers.ModelSerializer):
    """Read-only serializer for evaluation evidence."""
    
    class Meta:
        model = EvaluationEvidence
        fields = [
            'id',
            'evidence_type',
            'target_path',
            'captured_data',
            'content_hash',
            'content_snippet',
            'created_at',
        ]
        read_only_fields = fields


class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for audit log entries."""
    
    actor_email = serializers.CharField(source='actor.email', read_only=True, allow_null=True)
    target_type = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'actor',
            'actor_email',
            'action',
            'description',
            'target_type',
            'object_id',
            'metadata',
            'ip_address',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_target_type(self, obj):
        """Return the content type name if available."""
        if obj.content_type:
            return obj.content_type.model
        return None
