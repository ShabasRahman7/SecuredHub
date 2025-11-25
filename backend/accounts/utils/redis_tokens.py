"""
Redis-based invite token management utility.
Provides 24-hour auto-expiring tokens for tenant invitations.
"""
from django.core.cache import cache
import uuid
import logging

logger = logging.getLogger('api')


class InviteTokenManager:
    """Manage invite tokens in Redis with 24-hour auto-expiration."""
    
    TOKEN_PREFIX = "invite_token:"
    TOKEN_TTL = 86400  # 24 hours in seconds
    
    @classmethod
    def create_token(cls, email):
        """
        Create a new token and store in Redis with 24h TTL.
        
        Args:
            email: Email address associated with this invite
            
        Returns:
            str: UUID token
        """
        token = str(uuid.uuid4())
        cache_key = f"{cls.TOKEN_PREFIX}{token}"
        
        try:
            cache.set(cache_key, email, timeout=cls.TOKEN_TTL)
            logger.info(f"Created invite token in Redis for {email} (expires in 24h)")
            return token
        except Exception as e:
            logger.error(f"Failed to create token in Redis: {str(e)}")
            # Fallback to returning token even if Redis fails
            return token
    
    @classmethod
    def verify_token(cls, token):
        """
        Verify token and return associated email.
        
        Args:
            token: UUID token string
            
        Returns:
            str|None: Email if valid, None if expired/invalid
        """
        cache_key = f"{cls.TOKEN_PREFIX}{token}"
        
        try:
            email = cache.get(cache_key)
            if email:
                logger.info(f"Token verified in Redis for {email}")
            else:
                logger.warning(f"Token not found or expired in Redis: {token[:8]}...")
            return email
        except Exception as e:
            logger.error(f"Failed to verify token in Redis: {str(e)}")
            return None
    
    @classmethod
    def delete_token(cls, token):
        """
        Delete token from Redis.
        
        Args:
            token: UUID token string
        """
        cache_key = f"{cls.TOKEN_PREFIX}{token}"
        
        try:
            cache.delete(cache_key)
            logger.info(f"Deleted token from Redis: {token[:8]}...")
        except Exception as e:
            logger.error(f"Failed to delete token from Redis: {str(e)}")
    
    @classmethod
    def get_ttl(cls, token):
        """
        Get remaining TTL for a token.
        
        Args:
            token: UUID token string
            
        Returns:
            int: Remaining seconds, or 0 if expired/invalid
        """
        cache_key = f"{cls.TOKEN_PREFIX}{token}"
        
        try:
            # Django's cache doesn't have native TTL command
            # We check if key exists, if so it hasn't expired
            if cache.get(cache_key):
                return cls.TOKEN_TTL  # Approximate
            return 0
        except Exception as e:
            logger.error(f"Failed to get TTL from Redis: {str(e)}")
            return 0
