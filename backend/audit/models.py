from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditLog(models.Model):
    EVENT_TYPES = [
        ('scan.completed', 'Scan Completed'),
        ('scan.failed', 'Scan Failed'),
        ('scan.started', 'Scan Started'),
        ('user.login', 'User Login'),
        ('user.logout', 'User Logout'),
        ('user.created', 'User Created'),
        ('repo.added', 'Repository Added'),
        ('repo.deleted', 'Repository Deleted'),
        ('member.invited', 'Member Invited'),
        ('member.removed', 'Member Removed'),
        ('tenant.created', 'Tenant Created'),
        ('settings.changed', 'Settings Changed'),
        ('webhook.received', 'Webhook Received'),
    ]
    
    event_type = models.CharField(max_length=64, choices=EVENT_TYPES, db_index=True)
    actor_id = models.IntegerField(null=True, blank=True, db_index=True)
    actor_email = models.CharField(max_length=255, blank=True)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.IntegerField(null=True, blank=True)
    target_name = models.CharField(max_length=255, blank=True)
    tenant_id = models.IntegerField(null=True, blank=True, db_index=True)
    tenant_name = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['tenant_id', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} by {self.actor_email} at {self.created_at}"
