"""
Unmanaged models for compliance evaluation.

These models mirror the backend's compliance tables (managed=False)
allowing the worker to read/write to them without managing migrations.
"""
from django.db import models


class Tenant(models.Model):
    """Mirror of accounts.Tenant for FK references."""
    name = models.CharField(max_length=255)
    
    class Meta:
        managed = False
        db_table = 'organizations'


class User(models.Model):
    """Mirror of accounts.User for FK references."""
    email = models.EmailField()
    
    class Meta:
        managed = False
        db_table = 'users'


class Repository(models.Model):
    """Mirror of repositories.Repository."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    default_branch = models.CharField(max_length=100, default='main')
    
    class Meta:
        managed = False
        db_table = 'repositories'


class TenantCredential(models.Model):
    """Mirror of repositories.TenantCredential for access token retrieval."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20)
    encrypted_access_token = models.TextField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        managed = False
        db_table = 'tenant_credentials'


class ComplianceStandard(models.Model):
    """Mirror of standards.ComplianceStandard."""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100)
    version = models.CharField(max_length=20)
    is_builtin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        managed = False
        db_table = 'std_compliance_standards'


class ComplianceRule(models.Model):
    """Mirror of standards.ComplianceRule."""
    standard = models.ForeignKey(
        ComplianceStandard,
        on_delete=models.CASCADE,
        related_name='rules'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=30)
    check_config = models.JSONField(default=dict)
    weight = models.PositiveIntegerField(default=5)
    severity = models.CharField(max_length=20, default='medium')
    remediation_hint = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        managed = False
        db_table = 'std_compliance_rules'


class ComplianceEvaluation(models.Model):
    """Mirror of compliance.ComplianceEvaluation."""
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    
    repository = models.ForeignKey(
        Repository, 
        on_delete=models.CASCADE,
        related_name='evaluations'
    )
    standard = models.ForeignKey(
        ComplianceStandard,
        on_delete=models.CASCADE,
        related_name='evaluations'
    )
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    commit_hash = models.CharField(max_length=40, null=True, blank=True)
    branch = models.CharField(max_length=100, default='main')
    error_message = models.TextField(null=True, blank=True)
    task_id = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'cpl_evaluations'
    
    def __str__(self):
        return f"Eval #{self.id} - {self.repository.name}"


class RuleResult(models.Model):
    """Mirror of compliance.RuleResult."""
    evaluation = models.ForeignKey(
        ComplianceEvaluation,
        on_delete=models.CASCADE,
        related_name='rule_results'
    )
    rule = models.ForeignKey(
        ComplianceRule,
        on_delete=models.CASCADE,
        related_name='results'
    )
    passed = models.BooleanField()
    evidence = models.JSONField(default=dict)
    message = models.TextField(blank=True)
    weight = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = False
        db_table = 'cpl_rule_results'


class ComplianceScore(models.Model):
    """Mirror of compliance.ComplianceScore."""
    evaluation = models.OneToOneField(
        ComplianceEvaluation,
        on_delete=models.CASCADE,
        related_name='score',
        primary_key=True
    )
    total_score = models.DecimalField(max_digits=5, decimal_places=2)
    passed_weight = models.PositiveIntegerField()
    total_weight = models.PositiveIntegerField()
    passed_count = models.PositiveIntegerField()
    failed_count = models.PositiveIntegerField()
    total_rules = models.PositiveIntegerField()
    previous_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = False
        db_table = 'cpl_scores'
