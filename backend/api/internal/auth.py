"""
Service token authentication for internal API calls.

Used for worker → backend communication.
"""
import os
from rest_framework import authentication, exceptions
from rest_framework.permissions import BasePermission


class ServiceTokenAuthentication(authentication.BaseAuthentication):
    """
    Authenticates requests from internal services using X-Service-Token header.
    
    Token is validated against INTERNAL_SERVICE_TOKEN environment variable.
    This is used for service-to-service communication (e.g., worker → backend).
    """
    
    HEADER_NAME = 'HTTP_X_SERVICE_TOKEN'
    
    def authenticate(self, request):
        """
        Authenticate the request and return a tuple of (None, token) or None.
        
        Returns None for user since this is service auth, not user auth.
        """
        token = request.META.get(self.HEADER_NAME)
        
        if not token:
            return None
        
        expected_token = os.getenv('INTERNAL_SERVICE_TOKEN', '')
        
        if not expected_token:
            raise exceptions.AuthenticationFailed(
                'Internal service authentication not configured'
            )
        
        if token != expected_token:
            raise exceptions.AuthenticationFailed('Invalid service token')
        
        # Return None for user, token for auth info
        # This indicates successful service auth without a user context
        return (None, token)
    
    def authenticate_header(self, request):
        """Return header to indicate how to authenticate."""
        return 'ServiceToken'


class IsInternalService(BasePermission):
    """
    Permission class to check if request is from an internal service.
    """
    
    def has_permission(self, request, view):
        # Check if ServiceTokenAuthentication was used
        return request.auth is not None
