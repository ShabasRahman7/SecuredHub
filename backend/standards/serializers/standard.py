"""
Serializers for standards API.
"""
from rest_framework import serializers
from standards.models import ComplianceStandard, ComplianceRule, RepositoryStandard


class ComplianceRuleSerializer(serializers.ModelSerializer):
    """Serializer for compliance rules."""
    
    class Meta:
        model = ComplianceRule
        fields = [
            'id', 'name', 'description', 'rule_type', 'check_config',
            'weight', 'severity', 'remediation_hint', 'order', 'is_active'
        ]
        read_only_fields = ['id']


class ComplianceStandardListSerializer(serializers.ModelSerializer):
    """List serializer for compliance standards (minimal data)."""
    rule_count = serializers.IntegerField(read_only=True)
    total_weight = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ComplianceStandard
        fields = [
            'id', 'name', 'slug', 'description', 'version',
            'is_builtin', 'is_active', 'rule_count', 'total_weight'
        ]


class ComplianceStandardDetailSerializer(serializers.ModelSerializer):
    """Detail serializer for compliance standards (includes rules)."""
    rules = ComplianceRuleSerializer(many=True, read_only=True)
    rule_count = serializers.IntegerField(read_only=True)
    total_weight = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ComplianceStandard
        fields = [
            'id', 'name', 'slug', 'description', 'version',
            'is_builtin', 'is_active', 'rule_count', 'total_weight',
            'rules', 'created_at', 'updated_at'
        ]


class RepositoryStandardSerializer(serializers.ModelSerializer):
    """Serializer for repository-standard assignments."""
    standard_name = serializers.CharField(source='standard.name', read_only=True)
    standard_version = serializers.CharField(source='standard.version', read_only=True)
    assigned_by_email = serializers.CharField(source='assigned_by.email', read_only=True)
    
    class Meta:
        model = RepositoryStandard
        fields = [
            'id', 'repository', 'standard', 'standard_name', 'standard_version',
            'assigned_by', 'assigned_by_email', 'is_active', 'assigned_at'
        ]
        read_only_fields = ['id', 'assigned_at', 'assigned_by']


class AssignStandardSerializer(serializers.Serializer):
    """Serializer for assigning a standard to a repository."""
    standard_id = serializers.IntegerField()
    
    def validate_standard_id(self, value):
        if not ComplianceStandard.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Standard not found or not active")
        return value


class CreateStandardSerializer(serializers.ModelSerializer):
    """Serializer for creating a new custom standard."""
    tenant = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = ComplianceStandard
        fields = ['name', 'description', 'tenant']
    
    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters")
        return value
    
    def create(self, validated_data):
        from django.utils.text import slugify
        from accounts.models import Tenant
        import uuid
        
        tenant_id = validated_data.pop('tenant', None)
        name = validated_data.get('name')
        
        # Generate unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while ComplianceStandard.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        validated_data['slug'] = slug
        validated_data['is_builtin'] = False
        
        if tenant_id:
            validated_data['organization'] = Tenant.objects.get(id=tenant_id)
        
        return super().create(validated_data)


class UpdateStandardSerializer(serializers.ModelSerializer):
    """Serializer for updating a custom standard."""
    
    class Meta:
        model = ComplianceStandard
        fields = ['name', 'description', 'is_active']
    
    def validate(self, data):
        if self.instance and self.instance.is_builtin:
            raise serializers.ValidationError("Cannot modify built-in standards")
        return data


class CreateRuleSerializer(serializers.ModelSerializer):
    """Serializer for creating a new rule in a custom standard."""
    
    class Meta:
        model = ComplianceRule
        fields = [
            'name', 'description', 'rule_type', 'check_config',
            'weight', 'severity', 'remediation_hint', 'order'
        ]
    
    def validate_rule_type(self, value):
        allowed_types = ['file_exists', 'file_forbidden', 'folder_exists', 
                         'pattern_match', 'config_check', 'hygiene']
        if value not in allowed_types:
            raise serializers.ValidationError(f"Invalid rule type. Must be one of: {', '.join(allowed_types)}")
        return value
    
    def validate_check_config(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("check_config must be a JSON object")
        return value

