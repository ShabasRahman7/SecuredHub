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
