# database models
from rest_framework import serializers
from .models import Scan, ScanFinding

class ScanFindingSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ScanFinding
        fields = [
            'id', 'scan', 'tool', 'rule_id', 'title', 'description',
            'severity', 'file_path', 'line_number', 'raw_output', 
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class ScanSerializer(serializers.ModelSerializer):
    findings_count = serializers.SerializerMethodField()
    severity_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Scan
        fields = [
            'id', 'repository', 'triggered_by', 'status', 'started_at',
            'completed_at', 'commit_hash', 'branch', 'error_message',
            'created_at', 'findings_count', 'severity_summary'
        ]
        read_only_fields = ['id', 'created_at', 'findings_count', 'severity_summary']
    
    def get_findings_count(self, obj):
        return obj.findings.count()
    
    def get_severity_summary(self, obj):
        findings = obj.findings.all()
        return {
            'total': findings.count(),
            'critical': findings.filter(severity='critical').count(),
            'high': findings.filter(severity='high').count(),
            'medium': findings.filter(severity='medium').count(),
            'low': findings.filter(severity='low').count(),
        }

class ScanDetailSerializer(ScanSerializer):
    findings = ScanFindingSerializer(many=True, read_only=True)
    
    class Meta(ScanSerializer.Meta):
        fields = ScanSerializer.Meta.fields + ['findings']
