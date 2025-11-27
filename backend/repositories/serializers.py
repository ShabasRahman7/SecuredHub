from rest_framework import serializers
from .models import Repository


class RepositorySerializer(serializers.ModelSerializer):
    """
    Serializer for Repository listing and retrieval.
    """
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_id = serializers.IntegerField(source='tenant.id', read_only=True)
    
    class Meta:
        model = Repository
        fields = [
            'id', 'name', 'url', 'visibility', 'default_branch',
            'tenant_id', 'tenant_name',
            'is_active', 'last_scan_status', 'last_scan_at',
            'github_owner', 'github_full_name',
            'assigned_developers',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'tenant_id', 'tenant_name',
            'github_owner', 'github_full_name',
            'last_scan_status', 'last_scan_at',
            'created_at', 'updated_at'
        ]


class RepositoryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new repositories.
    Validates URL format and ensures HTTPS.
    """
    class Meta:
        model = Repository
        fields = ['name', 'url', 'visibility', 'default_branch']
    
    def validate_url(self, value):
        """Validate repository URL must use HTTPS."""
        if not value.startswith('https://'):
            raise serializers.ValidationError("Repository URL must use HTTPS protocol.")
        
        # Basic validation for common git hosting platforms
        valid_domains = ['github.com', 'gitlab.com', 'bitbucket.org']
        if not any(domain in value for domain in valid_domains):
            raise serializers.ValidationError(
                "Repository URL must be from a supported platform (GitHub, GitLab, or Bitbucket)."
            )
        
        return value
    
    def validate_name(self, value):
        """Validate repository name."""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Repository name must be at least 2 characters long.")
        return value.strip()
    
    def validate(self, data):
        """Cross-field validation."""
        # Ensure default_branch is set
        if not data.get('default_branch'):
            data['default_branch'] = 'main'
        
        return data


class RepositoryUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating repository details.
    """
    class Meta:
        model = Repository
        fields = ['name', 'visibility', 'default_branch', 'is_active', 'assigned_developers']
    
    def validate_name(self, value):
        """Validate repository name."""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Repository name must be at least 2 characters long.")
        return value.strip()
