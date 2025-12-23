from django.contrib import admin
from .models import ComplianceStandard, ComplianceRule, RepositoryStandard


class ComplianceRuleInline(admin.TabularInline):
    model = ComplianceRule
    extra = 0
    fields = ('name', 'rule_type', 'weight', 'severity', 'is_active', 'order')
    ordering = ('order', 'name')


@admin.register(ComplianceStandard)
class ComplianceStandardAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'is_builtin', 'organization', 'rule_count', 'is_active')
    list_filter = ('is_builtin', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ComplianceRuleInline]
    
    def rule_count(self, obj):
        return obj.rules.filter(is_active=True).count()
    rule_count.short_description = 'Rules'


@admin.register(ComplianceRule)
class ComplianceRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'standard', 'rule_type', 'weight', 'severity', 'is_active')
    list_filter = ('standard', 'rule_type', 'severity', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('standard', 'order', 'name')


@admin.register(RepositoryStandard)
class RepositoryStandardAdmin(admin.ModelAdmin):
    list_display = ('repository', 'standard', 'assigned_by', 'is_active', 'assigned_at')
    list_filter = ('standard', 'is_active')
    search_fields = ('repository__name', 'standard__name')
    raw_id_fields = ('repository', 'assigned_by')
