from django.contrib import admin
from audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'actor_email', 'target_name', 'tenant_name', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['actor_email', 'target_name', 'tenant_name']
    readonly_fields = ['event_type', 'actor_id', 'actor_email', 'target_type', 
                       'target_id', 'target_name', 'tenant_id', 'tenant_name',
                       'ip_address', 'user_agent', 'metadata', 'created_at']
    ordering = ['-created_at']
