"""
Models for audit logging and evidence storage.

This module defines:
- AuditLog: History of all compliance-related actions
- EvaluationEvidence: Repository snapshots captured during evaluations
"""
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class AuditLog(models.Model):
    """
    Audit log entry for tracking compliance-related actions.
    
    Records who did what, when, and to which object.
    Useful for compliance auditing and debugging.
    """
    
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_TRIGGER = 'trigger'
    ACTION_COMPLETE = 'complete'
    ACTION_FAIL = 'fail'
    ACTION_ASSIGN = 'assign'
    ACTION_UNASSIGN = 'unassign'
    
    ACTION_CHOICES = (
        (ACTION_CREATE, 'Created'),
        (ACTION_UPDATE, 'Updated'),
        (ACTION_DELETE, 'Deleted'),
        (ACTION_TRIGGER, 'Triggered'),
        (ACTION_COMPLETE, 'Completed'),
        (ACTION_FAIL, 'Failed'),
        (ACTION_ASSIGN, 'Assigned'),
        (ACTION_UNASSIGN, 'Unassigned'),
    )
    
    # Who performed the action
    actor = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text="User who performed the action"
    )
    
    # Which organization this log belongs to (for tenant isolation)
    organization = models.ForeignKey(
        'accounts.Tenant',
        on_delete=models.CASCADE,
        related_name='audit_logs',
        db_index=True,
        help_text="Organization this action belongs to"
    )
    
    # What action was performed
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True
    )
    
    # Generic relation to target object (evaluation, repository, standard, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('content_type', 'object_id')
    
    # Human-readable description
    description = models.TextField(
        help_text="Human-readable description of the action"
    )
    
    # Additional metadata (JSON)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context about the action"
    )
    
    # IP address for security auditing
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the actor"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'aud_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['actor', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        actor_str = self.actor.email if self.actor else 'System'
        return f"[{self.created_at}] {actor_str} {self.action}: {self.description[:50]}"


class EvaluationEvidence(models.Model):
    """
    Evidence captured during a compliance evaluation.
    
    Stores snapshots of repository state at evaluation time,
    providing audit trail for compliance verification.
    """
    
    EVIDENCE_TYPE_FILE_CHECK = 'file_check'
    EVIDENCE_TYPE_FOLDER_CHECK = 'folder_check'
    EVIDENCE_TYPE_CONFIG_CHECK = 'config_check'
    EVIDENCE_TYPE_REPO_METADATA = 'repo_metadata'
    EVIDENCE_TYPE_COMMIT_INFO = 'commit_info'
    
    EVIDENCE_TYPE_CHOICES = (
        (EVIDENCE_TYPE_FILE_CHECK, 'File Existence Check'),
        (EVIDENCE_TYPE_FOLDER_CHECK, 'Folder Existence Check'),
        (EVIDENCE_TYPE_CONFIG_CHECK, 'Configuration Check'),
        (EVIDENCE_TYPE_REPO_METADATA, 'Repository Metadata'),
        (EVIDENCE_TYPE_COMMIT_INFO, 'Commit Information'),
    )
    
    evaluation = models.ForeignKey(
        'compliance.ComplianceEvaluation',
        on_delete=models.CASCADE,
        related_name='evidence',
        db_index=True
    )
    
    evidence_type = models.CharField(
        max_length=30,
        choices=EVIDENCE_TYPE_CHOICES,
        db_index=True
    )
    
    # Path or identifier for the checked item
    target_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="File path or identifier being checked"
    )
    
    # Captured data
    # Examples:
    # - File check: {"exists": true, "size_bytes": 1234, "last_modified": "..."}
    # - Config check: {"key": "license", "value": "MIT", "file": "package.json"}
    # - Repo metadata: {"default_branch": "main", "stars": 100, "forks": 20}
    captured_data = models.JSONField(
        default=dict,
        help_text="Data captured during the check"
    )
    
    # Optional content hash for integrity verification
    content_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 hash of file content (for file checks)"
    )
    
    # For small files, we might store a snippet
    content_snippet = models.TextField(
        blank=True,
        help_text="First N characters of file content (for documentation files)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'aud_evidence'
        verbose_name = 'Evaluation Evidence'
        verbose_name_plural = 'Evaluation Evidence'
        ordering = ['evaluation', 'evidence_type', 'target_path']
        indexes = [
            models.Index(fields=['evaluation', 'evidence_type']),
        ]
    
    def __str__(self):
        return f"Evidence: {self.evidence_type} - {self.target_path or 'N/A'}"
