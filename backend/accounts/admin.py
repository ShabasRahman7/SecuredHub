from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Tenant, TenantMember, TenantInvite, MemberInvite

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_by', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'created_by__email']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    ordering = ['-created_at']

@admin.register(TenantMember)
class TenantMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__email', 'tenant__name']
    ordering = ['-joined_at']

@admin.register(MemberInvite)
class MemberInviteAdmin(admin.ModelAdmin):
    list_display = ['email', 'tenant', 'status', 'invited_by', 'created_at', 'expires_at']
    list_filter = ['status', 'created_at']
    search_fields = ['email', 'tenant__name', 'invited_by__email']
    readonly_fields = ['token', 'created_at', 'accepted_at']
    ordering = ['-created_at']

@admin.register(TenantInvite)
class TenantInviteAdmin(admin.ModelAdmin):
    list_display = ['email', 'status', 'invited_by', 'invited_at', 'expires_at']
    list_filter = ['status', 'invited_at']
    search_fields = ['email', 'invited_by__email']
    readonly_fields = ['token', 'invited_at', 'registered_at']
    ordering = ['-invited_at']
