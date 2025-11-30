from rest_framework import serializers
from .models import Scan, ScanFinding

class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = [
            "id", "status", "branch", "commit_hash",
            "started_at", "completed_at", "created_at"
        ]

class ScanFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanFinding
        fields = "__all__"
