"""
Serializers for internal API (worker → backend communication).
"""
from rest_framework import serializers
from compliance.models import ComplianceEvaluation, RuleResult, ComplianceScore


class UpdateStatusSerializer(serializers.Serializer):
    """Serializer for updating evaluation status."""
    
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    message = serializers.CharField(max_length=500, required=False, allow_blank=True)
    progress = serializers.IntegerField(min_value=0, max_value=100, required=False)
    commit_hash = serializers.CharField(max_length=40, required=False, allow_blank=True)
    error_message = serializers.CharField(required=False, allow_blank=True)
    task_id = serializers.CharField(max_length=255, required=False, allow_blank=True)


class RuleResultItemSerializer(serializers.Serializer):
    """Serializer for a single rule result item."""
    
    rule_id = serializers.IntegerField()
    passed = serializers.BooleanField()
    message = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    evidence = serializers.JSONField(required=False, default=dict)
    weight = serializers.IntegerField(min_value=1, max_value=10)


class BulkRuleResultSerializer(serializers.Serializer):
    """Serializer for bulk creating rule results."""
    
    results = RuleResultItemSerializer(many=True)
    
    def validate_results(self, value):
        if not value:
            raise serializers.ValidationError("At least one result is required")
        if len(value) > 500:
            raise serializers.ValidationError("Maximum 500 results per request")
        return value


class CompleteEvaluationSerializer(serializers.Serializer):
    """Serializer for completing an evaluation with score."""
    
    passed_weight = serializers.IntegerField(min_value=0)
    total_weight = serializers.IntegerField(min_value=0)
    passed_count = serializers.IntegerField(min_value=0)
    failed_count = serializers.IntegerField(min_value=0)
    total_rules = serializers.IntegerField(min_value=0)
    
    def validate(self, data):
        if data['passed_count'] + data['failed_count'] != data['total_rules']:
            raise serializers.ValidationError(
                "passed_count + failed_count must equal total_rules"
            )
        if data['passed_weight'] > data['total_weight']:
            raise serializers.ValidationError(
                "passed_weight cannot exceed total_weight"
            )
        return data


class EvaluationStatusResponseSerializer(serializers.ModelSerializer):
    """Response serializer for evaluation status updates."""
    
    class Meta:
        model = ComplianceEvaluation
        fields = ['id', 'status', 'started_at', 'completed_at', 'error_message']
