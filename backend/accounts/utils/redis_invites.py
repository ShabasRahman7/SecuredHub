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
    
    # prefixes for different invite types
    MEMBER_INVITE_PREFIX = "invite:member:token:"
    MEMBER_EMAIL_PREFIX = "invite:member:email:"
    TENANT_INVITE_PREFIX = "invite:tenant:token:"
    TENANT_EMAIL_PREFIX = "invite:tenant:email:"
    
    DEFAULT_EXPIRY_HOURS = 24  # 24 hours for all invite types
    
    @classmethod
    def create_member_invite(cls, tenant_id, email, invited_by_id, role='developer', expiry_hours=None):
        # creating a new member invite token in Redis (Owner → Developer).
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
        # creating a new tenant invite token in Redis (Admin → Tenant Owner).
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
    
    @classmethod
    def create_invite(cls, tenant_id, email, invited_by_id, role='developer', expiry_hours=None):
        """Backward compatibility - creates member invite."""
        return cls.create_member_invite(tenant_id, email, invited_by_id, role, expiry_hours)
    
    @classmethod
    def get_invite_by_token(cls, token, invite_type=None):
        # retrieving invite data by token.
        if invite_type == 'member':
            prefixes = [cls.MEMBER_INVITE_PREFIX]
        elif invite_type == 'tenant':
            prefixes = [cls.TENANT_INVITE_PREFIX]
        else:
            # try both types
            prefixes = [cls.MEMBER_INVITE_PREFIX, cls.TENANT_INVITE_PREFIX]
        
        for prefix in prefixes:
            token_key = f"{prefix}{token}"
            try:
                data = cache.get(token_key)
            except Exception:
                # if cache backend is unavailable (e.g., Redis down), treat as missing
                data = None
            if data:
                return json.loads(data)
        
        return None
    
    @classmethod
    def get_member_invite_by_email(cls, tenant_id, email):
        # checking if there's an active member invite for this email in this tenant.
        email_key = f"{cls.MEMBER_EMAIL_PREFIX}{tenant_id}:{email}"
        try:
            token = cache.get(email_key)
        except Exception:
            token = None
        
        if token:
            return cls.get_invite_by_token(token, invite_type='member')
        return None
    
    @classmethod
    def get_tenant_invite_by_email(cls, email):
        # checking if there's an active tenant invite for this email.
        email_key = f"{cls.TENANT_EMAIL_PREFIX}{email}"
        try:
            token = cache.get(email_key)
        except Exception:
            token = None
        
        if token:
            return cls.get_invite_by_token(token, invite_type='tenant')
        return None
    
    @classmethod
    def get_invite_by_email(cls, tenant_id, email):
        """Backward compatibility - gets member invite."""
        return cls.get_member_invite_by_email(tenant_id, email)
    
    @classmethod
    def delete_invite(cls, token):
        # deleting an invite token from Redis.
        # getting invite data first to delete email key
        invite_data = cls.get_invite_by_token(token)
        
        if invite_data:
            invite_type = invite_data.get('type', 'member')
            
            if invite_type == 'member':
                # deleting member invite keys
                token_key = f"{cls.MEMBER_INVITE_PREFIX}{token}"
                email_key = f"{cls.MEMBER_EMAIL_PREFIX}{invite_data['tenant_id']}:{invite_data['email']}"
            else:
                # deleting tenant invite keys
                token_key = f"{cls.TENANT_INVITE_PREFIX}{token}"
                email_key = f"{cls.TENANT_EMAIL_PREFIX}{invite_data['email']}"
            
            try:
                cache.delete(token_key)
                cache.delete(email_key)
            except Exception:
                # ignoring cache delete errors
                pass
            
            return True
        return False
    
    @classmethod
    def mark_accepted(cls, token):
        # mark an invite as accepted (deletes it from Redis).
        return cls.delete_invite(token)
    
    @classmethod
    def list_member_invites(cls, tenant_id):

        invites = []
        
        # getting all member invite tokens
        pattern = f"{cls.MEMBER_INVITE_PREFIX}*"
        try:
            keys = cache.keys(pattern) if hasattr(cache, 'keys') else []
        except Exception:
            keys = []
        
        for key in keys:
            try:
                data = cache.get(key)
            except Exception:
                data = None
            if data:
                invite_data = json.loads(data)
                if invite_data.get('tenant_id') == tenant_id:
                    invites.append(invite_data)
        
        return invites
    
    @classmethod
    def list_all_tenant_invites(cls):
        # list all active tenant invites (Admin → Tenant Owner).
        invites = []
        
        # getting all tenant invite tokens
        pattern = f"{cls.TENANT_INVITE_PREFIX}*"
        try:
            keys = cache.keys(pattern) if hasattr(cache, 'keys') else []
        except Exception:
            keys = []
        
        for key in keys:
            try:
                data = cache.get(key)
            except Exception:
                data = None
            if data:
                invites.append(json.loads(data))
        
        return invites
    
    @classmethod
    def list_tenant_invites(cls, tenant_id):
        """Backward compatibility - lists member invites."""
        return cls.list_member_invites(tenant_id)
    
    @classmethod
    def is_expired(cls, invite_data):
        # checking if an invite is expired.
        if not invite_data:
            return True
        
        expires_at = timezone.datetime.fromisoformat(invite_data['expires_at'])
        return timezone.now() > expires_at
