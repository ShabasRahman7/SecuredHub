from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid


class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model using email authentication.
    Role determined by is_staff (admin) or TenantMember.role (owner/developer).
    """
    username = None  # Remove username field
    email = models.EmailField(unique=True, db_index=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # No additional required fields

    objects = CustomUserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email
    
    def get_role(self):
        """Get user's role - admin or tenant role"""
        if self.is_staff:
            return 'admin'
        
        # Since user can only belong to one tenant, use OneToOne relationship
        if hasattr(self, 'tenant_membership') and self.tenant_membership:
            return self.tenant_membership.role
        return None


class Tenant(models.Model):
    """
    Tenant model for multi-tenant architecture.
    Each organization represents a separate tenant in the SaaS platform.
    """
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_organizations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organizations'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Organizations'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Tenant.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class TenantMember(models.Model):
    """
    Membership model linking users to organizations with roles.
    Implements role-based access control (RBAC).
    
    IMPORTANT: Each user can only belong to ONE tenant.
    This ensures simple security model and clear ownership.
    """
    ROLE_OWNER = 'owner'
    ROLE_DEVELOPER = 'developer'
    
    ROLE_CHOICES = (
        (ROLE_OWNER, 'Owner'),
        (ROLE_DEVELOPER, 'Developer'),
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='tenant_membership'  # Changed to singular
    )
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, db_index=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenant_members'
        verbose_name = 'Tenant Member'
        verbose_name_plural = 'Tenant Members'
        unique_together = ('tenant', 'user')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} → {self.tenant.name} ({self.role})"

    def is_owner(self):
        """Check if member is an owner."""
        return self.role == self.ROLE_OWNER

    def is_developer(self):
        """Check if member is a developer."""
        return self.role == self.ROLE_DEVELOPER


class MemberInvite(models.Model):
    """
    Invitation for users to join a tenant organization.
    """
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_EXPIRED = 'expired'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_CANCELLED, 'Cancelled'),
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='member_invites'
    )
    email = models.EmailField(db_index=True)
    token = models.CharField(max_length=128, unique=True, db_index=True)
    role = models.CharField(
        max_length=32,
        choices=(
            (TenantMember.ROLE_DEVELOPER, 'Developer'),
        ),
        default=TenantMember.ROLE_DEVELOPER
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )
    
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_member_invites'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    # Resend tracking
    last_sent_at = models.DateTimeField(null=True, blank=True)
    resend_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'member_invites'
        verbose_name = 'Member Invite'
        verbose_name_plural = 'Member Invites'
        ordering = ['-created_at']

    def __str__(self):
        return f"Invite: {self.email} -> {self.tenant.name} ({self.status})"

    def save(self, *args, **kwargs):
        """Auto-generate token and expiration."""
        if not self.token:
            self.token = str(uuid.uuid4())
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return self.status == self.STATUS_PENDING and not self.is_expired()

    def mark_accepted(self):
        self.status = self.STATUS_ACCEPTED
        self.accepted_at = timezone.now()
        self.save()

    def mark_expired(self):
        self.status = self.STATUS_EXPIRED
        self.save()

    def mark_cancelled(self):
        self.status = self.STATUS_CANCELLED
        self.save()


class TenantInvite(models.Model):
    """
    Invitation for new tenants to join the platform (Admin -> Tenant).
    """
    STATUS_PENDING = 'pending'
    STATUS_REGISTERED = 'registered'
    STATUS_EXPIRED = 'expired'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_REGISTERED, 'Registered'),
        (STATUS_EXPIRED, 'Expired'),
    )
    
    email = models.EmailField(unique=True, db_index=True)
    token = models.UUIDField(unique=True, db_index=True, null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tenant_invites_sent'
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    registered_at = models.DateTimeField(null=True, blank=True)
    registered_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenant_invite_used'
    )
    
    class Meta:
        db_table = 'tenant_invites'
        verbose_name = 'Tenant Invite'
        verbose_name_plural = 'Tenant Invites'
        ordering = ['-invited_at']
    
    def __str__(self):
        return f"Tenant Invite: {self.email} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Auto-generate token and set expiration (24h)."""
        if not self.token:
            self.token = uuid.uuid4()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return self.status == self.STATUS_PENDING and not self.is_expired()
    
    def mark_registered(self, user):
        self.status = self.STATUS_REGISTERED
        self.registered_at = timezone.now()
        self.registered_user = user
        self.save()


class AccessRequest(models.Model):
    """
    Waitlist/Access Request for public users.
    """
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    )
    
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    company_name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'access_requests'
        verbose_name = 'Access Request'
        verbose_name_plural = 'Access Requests'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.email} - {self.company_name} ({self.status})"
