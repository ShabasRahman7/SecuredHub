from django.contrib import admin
from .models import ComplianceEvaluation, RuleResult, ComplianceScore


class RuleResultInline(admin.TabularInline):
    model = RuleResult
    extra = 0
    readonly_fields = ('rule', 'passed', 'weight', 'message', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class ComplianceScoreInline(admin.StackedInline):
    model = ComplianceScore
    can_delete = False
    readonly_fields = ('total_score', 'passed_weight', 'total_weight', 
                       'passed_count', 'failed_count', 'total_rules', 
                       'previous_score', 'created_at')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ComplianceEvaluation)
class ComplianceEvaluationAdmin(admin.ModelAdmin):
    list_display = ('id', 'repository', 'standard', 'status', 'get_score', 
                    'triggered_by', 'created_at')
    list_filter = ('status', 'standard', 'created_at')
    search_fields = ('repository__name', 'standard__name')
    readonly_fields = ('task_id', 'started_at', 'completed_at', 'duration_seconds')
    raw_id_fields = ('repository', 'triggered_by')
    inlines = [ComplianceScoreInline, RuleResultInline]
    
    def get_score(self, obj):
        if hasattr(obj, 'score'):
            return f"{obj.score.total_score}%"
        return "-"
    get_score.short_description = 'Score'


@admin.register(RuleResult)
class RuleResultAdmin(admin.ModelAdmin):
    list_display = ('evaluation', 'rule', 'passed', 'weight', 'created_at')
    list_filter = ('passed', 'rule__standard')
    search_fields = ('rule__name', 'message')
    raw_id_fields = ('evaluation', 'rule')


@admin.register(ComplianceScore)
class ComplianceScoreAdmin(admin.ModelAdmin):
    list_display = ('evaluation', 'total_score', 'grade', 'passed_count', 
                    'failed_count', 'total_rules', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('evaluation', 'total_score', 'passed_weight', 'total_weight',
                       'passed_count', 'failed_count', 'total_rules', 
                       'previous_score', 'score_change')
