from rest_framework import serializers
from repositories.models import TenantCredential


class CredentialSerializer(serializers.ModelSerializer):
    repositories_count = serializers.ReadOnlyField()
    
    class Meta:
        model = TenantCredential
        fields = [
            'id', 'name', 'provider', 'is_active', 'repositories_count',
            'created_at', 'updated_at', 'last_used_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_used_at', 'repositories_count']


class CredentialCreateSerializer(serializers.ModelSerializer):
    access_token = serializers.CharField(write_only=True)
    
    class Meta:
        model = TenantCredential
        fields = ['name', 'provider', 'access_token']
    
    def validate_name(self, value):
        """Validate credential name."""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Credential name must be at least 2 characters long.")
        return value.strip()