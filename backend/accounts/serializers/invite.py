"""
Serializer for TenantInvite model.
"""
from rest_framework import serializers
from ..models import TenantInvite


class TenantInviteSerializer(serializers.ModelSerializer):
    """Serializer for tenant invites."""
    invited_by_email = serializers.EmailField(source='invited_by.email', read_only=True)
    registered_user_email = serializers.EmailField(source='registered_user.email', read_only=True, allow_null=True)
    
    class Meta:
        model = TenantInvite
        fields = ['id', 'email', 'status', 'invited_by_email', 'invited_at', 'registered_at', 'registered_user_email']
        read_only_fields = ['id', 'invited_at', 'registered_at']
