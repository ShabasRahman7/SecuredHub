from django.contrib import admin
from .models import AuditLog, EvaluationEvidence


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'organization', 'actor', 'action', 'description_short')
    list_filter = ('action', 'organization', 'created_at')
    search_fields = ('description', 'actor__email')
    readonly_fields = ('actor', 'organization', 'action', 'content_type', 
                       'object_id', 'description', 'metadata', 'ip_address', 'created_at')
    date_hierarchy = 'created_at'
    
    def description_short(self, obj):
        return obj.description[:80] + '...' if len(obj.description) > 80 else obj.description
    description_short.short_description = 'Description'
    
    def has_add_permission(self, request):
        return False  # Audit logs should only be created programmatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should not be editable
    
    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs should not be deletable


@admin.register(EvaluationEvidence)
class EvaluationEvidenceAdmin(admin.ModelAdmin):
    list_display = ('evaluation', 'evidence_type', 'target_path', 'created_at')
    list_filter = ('evidence_type', 'created_at')
    search_fields = ('target_path',)
    readonly_fields = ('evaluation', 'evidence_type', 'target_path', 
                       'captured_data', 'content_hash', 'content_snippet', 'created_at')
    raw_id_fields = ('evaluation',)
    
    def has_add_permission(self, request):
        return False  # Evidence should only be created during evaluations
    
    def has_change_permission(self, request, obj=None):
        return False  # Evidence should not be editable
    
    def has_delete_permission(self, request, obj=None):
        return False  # Evidence should not be deletable
