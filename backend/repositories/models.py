from django.db import models
from accounts.models import Tenant, TenantMember
from cryptography.fernet import Fernet
from django.conf import settings
import base64

class TenantCredential(models.Model):
    
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
    
    # oAuth-specific fields
    encrypted_access_token = models.TextField(
        help_text="Encrypted OAuth access token"
    )
    
    # gitHub-specific oAuth data
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
    
    # permissions and scope
    granted_scopes = models.TextField(
        null=True, 
        blank=True,
        help_text="OAuth scopes granted (comma-separated)"
    )
    
    # oAuth metadata
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
        key = settings.REPOSITORY_ENCRYPTION_KEY
        if isinstance(key, str):
            return key.encode('utf-8')
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
    
    credential = models.ForeignKey(
        TenantCredential,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='repositories',
        help_text="Credential used for repository access"
    )
    
    last_scanned_commit = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text="SHA hash of the last scanned commit"
    )
    
    webhook_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="GitHub webhook ID for automatic scanning"
    )
    
    webhook_secret = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="HMAC secret for webhook signature validation"
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

class RepositoryAssignment(models.Model):
    
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name='assignments',
        db_index=True
    )
    
    member = models.ForeignKey(
        TenantMember,
        on_delete=models.CASCADE,
        related_name='repository_assignments',
        db_index=True,
        help_text="Developer assigned to this repository"
    )
    
    assigned_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_repositories',
        help_text="User who assigned this repository"
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'repository_assignments'
        verbose_name = 'Repository Assignment'
        verbose_name_plural = 'Repository Assignments'
        unique_together = ('repository', 'member')
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.member.user.email} → {self.repository.name}"