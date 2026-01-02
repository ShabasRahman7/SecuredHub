# stores notification history for users
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True
    )
    notification_type = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Type of notification (e.g., 'repo_assigned', 'scan_complete')"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata for the notification"
    )
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at'], name='notif_user_read_created'),
            models.Index(fields=['user', '-created_at'], name='notif_user_created'),
        ]
    
    def __str__(self):
        return f"{self.user.email}: {self.title} ({self.notification_type})"
    
    def mark_as_read(self):
        # only updating if currently unread to avoid unnecessary DB writes
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
    
    def mark_as_unread(self):
        if self.is_read:
            self.is_read = False
            self.save(update_fields=['is_read'])
