from django.contrib import admin
from .models import Repository


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'visibility', 'is_active', 'last_scan_status', 'created_at')
    list_filter = ('visibility', 'is_active', 'created_at')
    search_fields = ('name', 'url', 'tenant__name', 'github_owner')
    readonly_fields = ('created_at', 'updated_at', 'github_owner', 'github_full_name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tenant', 'name', 'url', 'visibility', 'default_branch', 'is_active')
        }),
        ('GitHub Integration', {
            'fields': ('github_repo_id', 'github_owner', 'github_full_name'),
            'classes': ('collapse',)
        }),
        ('Scanning Status', {
            'fields': ('last_scan_status', 'last_scan_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
