"""
Models for compliance standards and rules.

This module defines the core data structures for:
- ComplianceStandard: Named collections of rules (e.g., "Startup Best Practices", "SOC2-like")
- ComplianceRule: Individual checkable rules within a standard
- RepositoryStandard: Assignment of standards to repositories
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class ComplianceStandard(models.Model):
    """
    A named collection of compliance rules.
    
    Can be:
    - Built-in (is_builtin=True): Predefined standards like "Startup Best Practices"
    - Custom (is_builtin=False): Organization-specific standards
    """
    
    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Human-readable name of the standard"
    )
    
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-friendly identifier"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the standard's purpose"
    )
    
    version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Version of the standard"
    )
    
    is_builtin = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True if this is a platform-provided standard"
    )
    
    # For custom standards, link to the organization
    organization = models.ForeignKey(
        'accounts.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='custom_standards',
        help_text="Organization that created this custom standard (null for built-in)"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this standard is available for use"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'std_compliance_standards'
        verbose_name = 'Compliance Standard'
        verbose_name_plural = 'Compliance Standards'
        ordering = ['name']
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(is_builtin=True, organization__isnull=True) |
                    models.Q(is_builtin=False, organization__isnull=False)
                ),
                name='standard_builtin_or_org'
            )
        ]
    
    def __str__(self):
        return f"{self.name} (v{self.version})"
    
    @property
    def total_weight(self):
        """Sum of all rule weights in this standard."""
        return self.rules.filter(is_active=True).aggregate(
            total=models.Sum('weight')
        )['total'] or 0
    
    @property
    def rule_count(self):
        """Number of active rules in this standard."""
        return self.rules.filter(is_active=True).count()


class ComplianceRule(models.Model):
    """
    An individual checkable rule within a compliance standard.
    
    Rule types define what kind of check is performed:
    - file_exists: Check if a required file exists
    - file_forbidden: Check that a forbidden file does NOT exist
    - folder_exists: Check if a required folder exists
    - config_check: Check for specific configuration values
    - pattern_match: Check for patterns in files
    """
    
    RULE_TYPE_FILE_EXISTS = 'file_exists'
    RULE_TYPE_FILE_FORBIDDEN = 'file_forbidden'
    RULE_TYPE_FOLDER_EXISTS = 'folder_exists'
    RULE_TYPE_CONFIG_CHECK = 'config_check'
    RULE_TYPE_PATTERN_MATCH = 'pattern_match'
    RULE_TYPE_HYGIENE = 'hygiene'
    
    RULE_TYPE_CHOICES = (
        (RULE_TYPE_FILE_EXISTS, 'Required File'),
        (RULE_TYPE_FILE_FORBIDDEN, 'Forbidden File'),
        (RULE_TYPE_FOLDER_EXISTS, 'Required Folder'),
        (RULE_TYPE_CONFIG_CHECK, 'Configuration Check'),
        (RULE_TYPE_PATTERN_MATCH, 'Pattern Match'),
        (RULE_TYPE_HYGIENE, 'Repository Hygiene'),
    )
    
    SEVERITY_LOW = 'low'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_HIGH = 'high'
    SEVERITY_CRITICAL = 'critical'
    
    SEVERITY_CHOICES = (
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    )
    
    standard = models.ForeignKey(
        ComplianceStandard,
        on_delete=models.CASCADE,
        related_name='rules',
        db_index=True
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Short name of the rule"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Detailed explanation of why this rule matters"
    )
    
    rule_type = models.CharField(
        max_length=30,
        choices=RULE_TYPE_CHOICES,
        db_index=True,
        help_text="Type of check to perform"
    )
    
    # Rule configuration stored as JSON
    # Examples:
    # file_exists: {"path": "README.md"}
    # file_forbidden: {"path": ".env", "patterns": ["*.key", "secrets/*"]}
    # folder_exists: {"path": ".github/workflows"}
    # config_check: {"file": "package.json", "key": "license", "expected": "MIT"}
    check_config = models.JSONField(
        default=dict,
        help_text="Configuration for the rule check (JSON)"
    )
    
    weight = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Weight of this rule in score calculation (1-10)"
    )
    
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_MEDIUM,
        help_text="Importance level of this rule"
    )
    
    # Remediation guidance
    remediation_hint = models.TextField(
        blank=True,
        help_text="Guidance on how to fix a failed rule"
    )
    
    # Ordering within the standard
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within the standard"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this rule is enforced"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'std_compliance_rules'
        verbose_name = 'Compliance Rule'
        verbose_name_plural = 'Compliance Rules'
        ordering = ['standard', 'order', 'name']
        unique_together = ('standard', 'name')
    
    def __str__(self):
        return f"{self.standard.name}: {self.name}"


class RepositoryStandard(models.Model):
    """
    Assignment of a compliance standard to a repository.
    
    A repository can have multiple standards assigned.
    Evaluations are triggered against assigned standards.
    """
    
    repository = models.ForeignKey(
        'repositories.Repository',
        on_delete=models.CASCADE,
        related_name='assigned_standards',
        db_index=True
    )
    
    standard = models.ForeignKey(
        ComplianceStandard,
        on_delete=models.CASCADE,
        related_name='assigned_repositories',
        db_index=True
    )
    
    assigned_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='standard_assignments',
        help_text="User who assigned this standard"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this assignment is active"
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'std_repository_standards'
        verbose_name = 'Repository Standard'
        verbose_name_plural = 'Repository Standards'
        unique_together = ('repository', 'standard')
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.repository.name} ← {self.standard.name}"
