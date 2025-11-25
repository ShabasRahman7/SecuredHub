from rest_framework import serializers
from ..models import AccessRequest

class AccessRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRequest
        fields = ['id', 'full_name', 'email', 'company_name', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']
