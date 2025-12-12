from django.db import models
from accounts.models import Tenant
from cryptography.fernet import Fernet
from django.conf import settings
import base64


class TenantCredential(models.Model):
    """Tenant-level OAuth credentials for repository access."""
    
    PROVIDER_GITHUB = 'github'
    PROVIDER_GITLAB = 'gitlab'
    PROVIDER_BITBUCKET = 'bitbucket'
    PROVIDER_AZURE = 'azure'
    
    PROVIDER_CHOICES = (
        (PROVIDER_GITHUB, 'GitHub'),
        (PROVIDER_GITLAB, 'GitLab'),
        (PROVIDER_BITBUCKET, 'Bitbucket'),
        (PROVIDER_AZURE, 'Azure DevOps'),
    )
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='credentials',
        db_index=True
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Human-readable name for this credential"
    )
    
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default=PROVIDER_GITHUB,
        db_index=True
    )
    
    # OAuth-specific fields
    encrypted_access_token = models.TextField(
        help_text="Encrypted OAuth access token"
    )
    
    # GitHub-specific OAuth data
    github_installation_id = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="GitHub App installation ID"
    )
    
    github_account_login = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="GitHub account/organization login"
    )
    
    github_account_id = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="GitHub account/organization ID"
    )
    
    # Permissions and scope
    granted_scopes = models.TextField(
        null=True, 
        blank=True,
        help_text="OAuth scopes granted (comma-separated)"
    )
    
    # OAuth metadata
    oauth_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional OAuth metadata"
    )
    
    added_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_credentials'
    )
    
    is_active = models.BooleanField(default=True, db_index=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_credentials'
        verbose_name = 'Tenant Credential'
        verbose_name_plural = 'Tenant Credentials'
        ordering = ['-created_at']
        unique_together = ('tenant', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.provider}) - {self.tenant.name}"
    
    def _get_encryption_key(self):
        """Get encryption key for access tokens."""
        key = getattr(settings, 'REPOSITORY_ENCRYPTION_KEY', None)
        if not key:
            key = Fernet.generate_key()
        elif isinstance(key, str):
            key = key.encode('utf-8')
        return key
    
    def set_access_token(self, token: str):
        """Encrypt and store access token."""
        if not token:
            self.encrypted_access_token = ''
            return
        
        fernet = Fernet(self._get_encryption_key())
        encrypted_token = fernet.encrypt(token.encode())
        self.encrypted_access_token = base64.b64encode(encrypted_token).decode()
    
    def get_access_token(self) -> str:
        """Decrypt and return access token."""
        if not self.encrypted_access_token:
            return None
        
        try:
            fernet = Fernet(self._get_encryption_key())
            encrypted_token = base64.b64decode(self.encrypted_access_token.encode())
            return fernet.decrypt(encrypted_token).decode()
        except Exception:
            return None
    
    @property
    def has_access_token(self) -> bool:
        """Check if credential has an access token."""
        return bool(self.encrypted_access_token)
    
    @property
    def repositories_count(self) -> int:
        """Count of repositories using this credential."""
        return self.repositories.count()


class Repository(models.Model):
    """Simple repository model for multi-tenant management."""
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='repositories',
        db_index=True
    )
    
    name = models.CharField(max_length=255, db_index=True)
    url = models.URLField(max_length=500)
    default_branch = models.CharField(max_length=100, default='main')
    description = models.TextField(null=True, blank=True)
    
    # Link to credential for private repository access
    credential = models.ForeignKey(
        TenantCredential,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='repositories',
        help_text="Credential used for repository access"
    )
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'repositories'
        verbose_name = 'Repository'
        verbose_name_plural = 'Repositories'
        ordering = ['-created_at']
        unique_together = ('tenant', 'url')

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"