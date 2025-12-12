"""
Redis-based invite token management.
Tokens are stored in Redis with automatic expiration instead of database.
Handles both tenant invites (admin → owner) and member invites (owner → developer).
"""
import uuid
import json
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone


class RedisInviteManager:
    """Manage invite tokens in Redis with automatic expiration."""
    
    # Prefixes for different invite types
    MEMBER_INVITE_PREFIX = "invite:member:token:"
    MEMBER_EMAIL_PREFIX = "invite:member:email:"
    TENANT_INVITE_PREFIX = "invite:tenant:token:"
    TENANT_EMAIL_PREFIX = "invite:tenant:email:"
    
    DEFAULT_EXPIRY_HOURS = 24  # 24 hours for all invite types
    
    @classmethod
    def create_member_invite(cls, tenant_id, email, invited_by_id, role='developer', expiry_hours=None):
        """
        Create a new member invite token in Redis (Owner → Developer).
        
        Args:
            tenant_id: ID of the tenant
            email: Email address to invite
            invited_by_id: ID of user who sent invite
            role: Role to assign (default: developer)
            expiry_hours: Hours until expiration (default: 24)
        
        Returns:
            dict: Invite data with token
        """
        expiry_hours = expiry_hours or cls.DEFAULT_EXPIRY_HOURS
        token = str(uuid.uuid4())
        
        invite_data = {
            'token': token,
            'type': 'member',
            'tenant_id': tenant_id,
            'email': email,
            'invited_by_id': invited_by_id,
            'role': role,
            'created_at': timezone.now().isoformat(),
            'expires_at': (timezone.now() + timedelta(hours=expiry_hours)).isoformat(),
            'status': 'pending'
        }
        
        token_key = f"{cls.MEMBER_INVITE_PREFIX}{token}"
        timeout_seconds = expiry_hours * 60 * 60
        cache.set(token_key, json.dumps(invite_data), timeout=timeout_seconds)
        
        email_key = f"{cls.MEMBER_EMAIL_PREFIX}{tenant_id}:{email}"
        cache.set(email_key, token, timeout=timeout_seconds)
        
        return invite_data
    
    @classmethod
    def create_tenant_invite(cls, email, invited_by_id, expiry_hours=None):
        """
        Create a new tenant invite token in Redis (Admin → Tenant Owner).
        
        Args:
            email: Email address to invite
            invited_by_id: ID of admin who sent invite
            expiry_hours: Hours until expiration (default: 24)
        
        Returns:
            dict: Invite data with token
        """
        expiry_hours = expiry_hours or cls.DEFAULT_EXPIRY_HOURS
        token = str(uuid.uuid4())
        
        invite_data = {
            'token': token,
            'type': 'tenant',
            'email': email,
            'invited_by_id': invited_by_id,
            'created_at': timezone.now().isoformat(),
            'expires_at': (timezone.now() + timedelta(hours=expiry_hours)).isoformat(),
            'status': 'pending'
        }
        
        token_key = f"{cls.TENANT_INVITE_PREFIX}{token}"
        timeout_seconds = expiry_hours * 60 * 60
        cache.set(token_key, json.dumps(invite_data), timeout=timeout_seconds)
        
        email_key = f"{cls.TENANT_EMAIL_PREFIX}{email}"
        cache.set(email_key, token, timeout=timeout_seconds)
        
        return invite_data
    
    # Backward compatibility
    @classmethod
    def create_invite(cls, tenant_id, email, invited_by_id, role='developer', expiry_hours=None):
        """Backward compatibility - creates member invite."""
        return cls.create_member_invite(tenant_id, email, invited_by_id, role, expiry_hours)
    
    @classmethod
    def get_invite_by_token(cls, token, invite_type=None):
        """
        Retrieve invite data by token.
        
        Args:
            token: Invite token
            invite_type: 'member' or 'tenant' (optional, will try both if not specified)
        
        Returns:
            dict or None: Invite data if found and valid
        """
        if invite_type == 'member':
            prefixes = [cls.MEMBER_INVITE_PREFIX]
        elif invite_type == 'tenant':
            prefixes = [cls.TENANT_INVITE_PREFIX]
        else:
            # Try both types
            prefixes = [cls.MEMBER_INVITE_PREFIX, cls.TENANT_INVITE_PREFIX]
        
        for prefix in prefixes:
            token_key = f"{prefix}{token}"
            data = cache.get(token_key)
            if data:
                return json.loads(data)
        
        return None
    
    @classmethod
    def get_member_invite_by_email(cls, tenant_id, email):
        """
        Check if there's an active member invite for this email in this tenant.
        
        Args:
            tenant_id: ID of the tenant
            email: Email address
        
        Returns:
            dict or None: Invite data if found
        """
        email_key = f"{cls.MEMBER_EMAIL_PREFIX}{tenant_id}:{email}"
        token = cache.get(email_key)
        
        if token:
            return cls.get_invite_by_token(token, invite_type='member')
        return None
    
    @classmethod
    def get_tenant_invite_by_email(cls, email):
        """
        Check if there's an active tenant invite for this email.
        
        Args:
            email: Email address
        
        Returns:
            dict or None: Invite data if found
        """
        email_key = f"{cls.TENANT_EMAIL_PREFIX}{email}"
        token = cache.get(email_key)
        
        if token:
            return cls.get_invite_by_token(token, invite_type='tenant')
        return None
    
    # Backward compatibility
    @classmethod
    def get_invite_by_email(cls, tenant_id, email):
        """Backward compatibility - gets member invite."""
        return cls.get_member_invite_by_email(tenant_id, email)
    
    @classmethod
    def delete_invite(cls, token):
        """
        Delete an invite token from Redis.
        
        Args:
            token: Invite token to delete
        
        Returns:
            bool: True if deleted, False if not found
        """
        # Get invite data first to delete email key
        invite_data = cls.get_invite_by_token(token)
        
        if invite_data:
            invite_type = invite_data.get('type', 'member')
            
            if invite_type == 'member':
                # Delete member invite keys
                token_key = f"{cls.MEMBER_INVITE_PREFIX}{token}"
                email_key = f"{cls.MEMBER_EMAIL_PREFIX}{invite_data['tenant_id']}:{invite_data['email']}"
            else:
                # Delete tenant invite keys
                token_key = f"{cls.TENANT_INVITE_PREFIX}{token}"
                email_key = f"{cls.TENANT_EMAIL_PREFIX}{invite_data['email']}"
            
            cache.delete(token_key)
            cache.delete(email_key)
            
            return True
        return False
    
    @classmethod
    def mark_accepted(cls, token):
        """
        Mark an invite as accepted (deletes it from Redis).
        
        Args:
            token: Invite token
        
        Returns:
            bool: True if marked, False if not found
        """
        return cls.delete_invite(token)
    
    @classmethod
    def list_member_invites(cls, tenant_id):
        """
        List all active member invites for a tenant.
        Note: This requires scanning Redis keys, which is not ideal for production.
        Consider storing a list of invite tokens per tenant if needed frequently.
        
        Args:
            tenant_id: ID of the tenant
        
        Returns:
            list: List of invite data dicts
        """
        invites = []
        
        # Get all member invite tokens
        pattern = f"{cls.MEMBER_INVITE_PREFIX}*"
        keys = cache.keys(pattern) if hasattr(cache, 'keys') else []
        
        for key in keys:
            data = cache.get(key)
            if data:
                invite_data = json.loads(data)
                if invite_data.get('tenant_id') == tenant_id:
                    invites.append(invite_data)
        
        return invites
    
    @classmethod
    def list_all_tenant_invites(cls):
        """
        List all active tenant invites (Admin → Tenant Owner).
        
        Returns:
            list: List of invite data dicts
        """
        invites = []
        
        # Get all tenant invite tokens
        pattern = f"{cls.TENANT_INVITE_PREFIX}*"
        keys = cache.keys(pattern) if hasattr(cache, 'keys') else []
        
        for key in keys:
            data = cache.get(key)
            if data:
                invites.append(json.loads(data))
        
        return invites
    
    # Backward compatibility
    @classmethod
    def list_tenant_invites(cls, tenant_id):
        """Backward compatibility - lists member invites."""
        return cls.list_member_invites(tenant_id)
    
    @classmethod
    def is_expired(cls, invite_data):
        """
        Check if an invite is expired.
        
        Args:
            invite_data: Invite data dict
        
        Returns:
            bool: True if expired
        """
        if not invite_data:
            return True
        
        expires_at = timezone.datetime.fromisoformat(invite_data['expires_at'])
        return timezone.now() > expires_at
