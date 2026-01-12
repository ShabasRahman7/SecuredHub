from rest_framework import serializers
from repositories.models import Repository, TenantCredential

class RepositorySerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    credential_name = serializers.CharField(source='credential.name', read_only=True, allow_null=True)
    last_scanned_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Repository
        fields = [
            'id', 'name', 'url', 'default_branch', 'description',
            'tenant_name', 'credential', 'credential_name', 'is_active',
            'last_scanned_commit', 'last_scanned_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant_name', 'credential_name', 'last_scanned_commit', 'last_scanned_at', 'created_at', 'updated_at']
    
    def get_last_scanned_at(self, obj):
        """Get the completion time of the latest completed scan."""
        last_scan = obj.scans.filter(status='completed').order_by('-completed_at').first()
        if last_scan and last_scan.completed_at:
            return last_scan.completed_at
        return None

class RepositoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = ['name', 'url', 'default_branch', 'description']
    
    def validate_url(self, value):
        tenant = self.context.get('tenant')
        if tenant and Repository.objects.filter(tenant=tenant, url=value, is_active=True).exists():
            raise serializers.ValidationError("A repository with this URL already exists in this tenant.")
        return value

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
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Credential name must be at least 2 characters long.")
        return value.strip()
