from django.core.cache import cache
import uuid

class InviteTokenManager:
    """Manage invite tokens in Redis with 24-hour auto-expiration."""
    
    TOKEN_PREFIX = "invite_token:"
    TOKEN_TTL = 86400  # 24 hours in seconds
    
    @classmethod
    def create_token(cls, email):
        # creating a new token and store in Redis with 24h TTL.
        token = str(uuid.uuid4())
        cache_key = f"{cls.TOKEN_PREFIX}{token}"
        
        try:
            cache.set(cache_key, email, timeout=cls.TOKEN_TTL)
            return token
        except Exception:
            return token
    
    @classmethod
    def verify_token(cls, token):
        # verifying token and return associated email.
        cache_key = f"{cls.TOKEN_PREFIX}{token}"
        
        try:
            email = cache.get(cache_key)
            return email
        except Exception:
            return None
    
    @classmethod
    def delete_token(cls, token):
        # deleting token from Redis.
        cache_key = f"{cls.TOKEN_PREFIX}{token}"
        
        try:
            cache.delete(cache_key)
        except Exception:
            pass
    
    @classmethod
    def get_ttl(cls, token):
        # getting remaining TTL for a token.
        cache_key = f"{cls.TOKEN_PREFIX}{token}"
        
        try:
            # django's cache doesn't have native TTL command
            # we check if key exists, if so it hasn't expired
            if cache.get(cache_key):
                return cls.TOKEN_TTL
            return 0
        except Exception:
            return 0
