"""
Serializers for compliance API.
"""
from rest_framework import serializers
from compliance.models import ComplianceEvaluation, RuleResult, ComplianceScore


class RuleResultSerializer(serializers.ModelSerializer):
    """Serializer for individual rule results."""
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    rule_type = serializers.CharField(source='rule.rule_type', read_only=True)
    severity = serializers.CharField(source='rule.severity', read_only=True)
    remediation_hint = serializers.CharField(source='rule.remediation_hint', read_only=True)
    
    class Meta:
        model = RuleResult
        fields = [
            'id', 'rule', 'rule_name', 'rule_type', 'passed', 
            'weight', 'severity', 'remediation_hint', 'message', 
            'evidence', 'created_at'
        ]


class ComplianceScoreSerializer(serializers.ModelSerializer):
    """Serializer for compliance scores."""
    grade = serializers.CharField(read_only=True)
    score_change = serializers.FloatField(read_only=True)
    
    class Meta:
        model = ComplianceScore
        fields = [
            'total_score', 'grade', 'passed_weight', 'total_weight',
            'passed_count', 'failed_count', 'total_rules',
            'previous_score', 'score_change', 'created_at'
        ]


class EvaluationListSerializer(serializers.ModelSerializer):
    """List serializer for evaluations (minimal data)."""
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    standard_name = serializers.CharField(source='standard.name', read_only=True)
    triggered_by_email = serializers.CharField(source='triggered_by.email', read_only=True)
    score = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceEvaluation
        fields = [
            'id', 'repository', 'repository_name', 'standard', 'standard_name',
            'status', 'triggered_by', 'triggered_by_email', 'score',
            'created_at', 'completed_at', 'branch', 'commit_hash'
        ]
    
    def get_score(self, obj):
        if hasattr(obj, 'score'):
            return float(obj.score.total_score)
        return None


class EvaluationDetailSerializer(serializers.ModelSerializer):
    """Detail serializer for evaluations (includes results)."""
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    standard_name = serializers.CharField(source='standard.name', read_only=True)
    triggered_by_email = serializers.CharField(source='triggered_by.email', read_only=True)
    score = ComplianceScoreSerializer(read_only=True)
    rule_results = RuleResultSerializer(many=True, read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)
    
    class Meta:
        model = ComplianceEvaluation
        fields = [
            'id', 'repository', 'repository_name', 'standard', 'standard_name',
            'status', 'triggered_by', 'triggered_by_email',
            'created_at', 'started_at', 'completed_at', 'duration_seconds',
            'branch', 'commit_hash', 'error_message',
            'score', 'rule_results'
        ]


class TriggerEvaluationSerializer(serializers.Serializer):
    """Serializer for triggering a new evaluation."""
    repository_id = serializers.IntegerField()
    standard_id = serializers.IntegerField()
    branch = serializers.CharField(max_length=100, default='main', required=False)
    
    def validate(self, data):
        from repositories.models import Repository
        from standards.models import ComplianceStandard, RepositoryStandard
        
        repository_id = data.get('repository_id')
        standard_id = data.get('standard_id')
        
        # Verify repository exists
        try:
            repository = Repository.objects.get(id=repository_id)
            data['repository'] = repository
        except Repository.DoesNotExist:
            raise serializers.ValidationError({'repository_id': 'Repository not found'})
        
        # Verify standard exists and is active
        try:
            standard = ComplianceStandard.objects.get(id=standard_id, is_active=True)
            data['standard'] = standard
        except ComplianceStandard.DoesNotExist:
            raise serializers.ValidationError({'standard_id': 'Standard not found or not active'})
        
        # Verify standard is assigned to repository
        if not RepositoryStandard.objects.filter(
            repository=repository,
            standard=standard,
            is_active=True
        ).exists():
            raise serializers.ValidationError({
                'standard_id': 'Standard is not assigned to this repository'
            })
        
        return data
