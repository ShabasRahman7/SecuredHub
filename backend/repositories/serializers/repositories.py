from rest_framework import serializers
from repositories.models import Repository


class RepositorySerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    credential_name = serializers.CharField(source='credential.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Repository
        fields = [
            'id', 'name', 'url', 'default_branch', 'description',
            'tenant_name', 'credential', 'credential_name', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant_name', 'credential_name', 'created_at', 'updated_at']
