from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

# email auth, no username needed
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        # normalizing to prevent case-sensitive duplicates
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

# using email for auth instead of username
class User(AbstractUser):
    username = None  # removing username field
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
        # admins skip tenant role system
        if self.is_staff:
            return 'admin'
        
        # one tenant per user
        if hasattr(self, 'tenant_membership') and self.tenant_membership:
            return self.tenant_membership.role
        return None

class Tenant(models.Model):
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
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deletion_scheduled_at = models.DateTimeField(null=True, blank=True, help_text="Scheduled permanent deletion date")

    class Meta:
        db_table = 'organizations'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Organizations'
        ordering = ['-created_at']
    
    @property
    def is_deleted(self):
        return self.deleted_at is not None
    
    def soft_delete(self):
        # keeping data for 30 days before permanent deletion
        self.deleted_at = timezone.now()
        self.is_active = False
        self.deletion_scheduled_at = timezone.now() + timedelta(days=30)
        self.save()
    
    def restore(self):
        self.deleted_at = None
        self.deletion_scheduled_at = None
        self.is_active = True
        self.save()

    def save(self, *args, **kwargs):
        # auto-generating URL-safe slug if not provided
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
    # one user = one tenant (RBAC model)
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
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deletion_scheduled_at = models.DateTimeField(null=True, blank=True, help_text="Scheduled permanent deletion date")

    class Meta:
        db_table = 'tenant_members'
        verbose_name = 'Tenant Member'
        verbose_name_plural = 'Tenant Members'
        unique_together = ('tenant', 'user')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} → {self.tenant.name} ({self.role})"

    def is_owner(self):
        return self.role == self.ROLE_OWNER

    def is_developer(self):
        return self.role == self.ROLE_DEVELOPER

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        # soft delete + disable user login
        from django.utils import timezone
        from datetime import timedelta

        self.deleted_at = timezone.now()
        # scheduling permanent deletion in 30 days
        self.deletion_scheduled_at = timezone.now() + timedelta(days=30)
        self.save(update_fields=['deleted_at', 'deletion_scheduled_at'])

        # disabling user login while member is soft-deleted
        if self.user.is_active:
            self.user.is_active = False
            self.user.save(update_fields=['is_active'])

    def restore(self):
        # restore + re-enable user login
        self.deleted_at = None
        self.deletion_scheduled_at = None
        self.save(update_fields=['deleted_at', 'deletion_scheduled_at'])

        if not self.user.is_active:
            self.user.is_active = True
            self.user.save(update_fields=['is_active'])

class MemberInvite(models.Model):
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
        # auto-generating token and expiration
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
        # auto-generating token, expires after 24h
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

