from django.contrib import admin
from .models import Repository, TenantCredential


@admin.register(TenantCredential)
class TenantCredentialAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'provider', 'is_active', 'repositories_count', 'created_at']
    list_filter = ['provider', 'is_active', 'created_at', 'tenant']
    search_fields = ['name', 'tenant__name']
    readonly_fields = ['created_at', 'updated_at', 'repositories_count', 'encrypted_access_token']
    
    fieldsets = (
        (None, {
            'fields': ('tenant', 'name', 'provider', 'added_by')
        }),
        ('Status', {
            'fields': ('is_active', 'last_used_at')
        }),
        ('Security', {
            'fields': ('encrypted_access_token',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'url', 'credential', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'tenant', 'credential']
    search_fields = ['name', 'url', 'tenant__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('tenant', 'name', 'url', 'default_branch', 'description')
        }),
        ('Access', {
            'fields': ('credential',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )