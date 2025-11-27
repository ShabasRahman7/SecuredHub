from django.db import models
from accounts.models import Tenant


class Repository(models.Model):
    """
    Repository model for multi-tenant repository management.
    Each repository belongs to exactly one organization and will be scanned by workers.
    """
    VISIBILITY_PUBLIC = 'public'
    VISIBILITY_PRIVATE = 'private'
    
    VISIBILITY_CHOICES = (
        (VISIBILITY_PUBLIC, 'Public'),
        (VISIBILITY_PRIVATE, 'Private'),
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='repositories',
        db_index=True
    )

    name = models.CharField(max_length=255, db_index=True)
    url = models.URLField(max_length=500)
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PUBLIC
    )
    default_branch = models.CharField(max_length=100, default='main')

    # Status tracking
    is_active = models.BooleanField(default=True)
    
    # Future: Scanning pipeline metadata
    last_scan_status = models.CharField(max_length=50, null=True, blank=True)
    last_scan_at = models.DateTimeField(null=True, blank=True)
    
    # Future: GitHub integration
    github_repo_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    github_owner = models.CharField(max_length=255, null=True, blank=True)
    github_full_name = models.CharField(max_length=500, null=True, blank=True)  # e.g., "owner/repo"
    
    assigned_developers = models.ManyToManyField(
        'accounts.User',
        related_name='assigned_repositories',
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'repositories'
        verbose_name = 'Repository'
        verbose_name_plural = 'Repositories'
        ordering = ['-created_at']
        unique_together = ('tenant', 'url')  # Same URL can't be added twice in same org
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['github_repo_id']),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"
    
    def extract_github_info(self):
        """
        Extract GitHub owner and repo name from URL.
        Example: https://github.com/owner/repo -> owner='owner', name='repo'
        """
        if 'github.com' in self.url:
            parts = self.url.rstrip('/').split('/')
            if len(parts) >= 2:
                self.github_owner = parts[-2]
                github_repo_name = parts[-1].replace('.git', '')
                self.github_full_name = f"{self.github_owner}/{github_repo_name}"
    
    def save(self, *args, **kwargs):
        """Auto-extract GitHub info before saving."""
        self.extract_github_info()
        super().save(*args, **kwargs)
