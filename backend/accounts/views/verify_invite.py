from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiTypes


@extend_schema(
    summary="Verify Tenant Invite Token",
    description="Verify a tenant invitation token before registration.",
    request={"application/json": {"token": "string"}},
    responses={200: OpenApiTypes.OBJECT},
    tags=["Authentication"]
)
@api_view(['POST'])
def verify_tenant_invite_token(request):
    """
    Verify a tenant invitation token.
    
    POST /api/v1/auth/verify-tenant-invite/
    Body: {"token": "uuid-string"}
    """
    from ..utils.email import verify_tenant_invite_token as verify_token
    
    token = request.data.get('token')
    
    if not token:
        return Response({
            "success": False,
            "error": {
                "message": "Token is required",
                "details": "Please provide an invitation token"
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    invite, error_message = verify_token(token)
    
    if error_message:
        return Response({
            "success": False,
            "error": {
                "message": "Invalid invitation",
                "details": error_message
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        "success": True,
        "message": "Invitation is valid",
        "email": invite.email,
        "expires_at": invite.expires_at.isoformat()
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Verify Invite Token (GET)",
    description="Verify an invite token (tenant or member) and return the associated email address.",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Authentication"]
)
@api_view(['GET'])
@permission_classes([AllowAny])
def verify_invite_token_get(request):
    """
    Verify an invite token from query parameter and return invited email.
    Supports both tenant invites (database) and member invites (Redis).
    
    GET /api/v1/auth/verify-invite/?token=XXX
    """
    from ..utils.email import verify_tenant_invite_token as verify_token
    from ..utils.redis_invites import RedisInviteManager
    
    token = request.GET.get('token')
    
    if not token:
        return Response({
            "success": False,
            "error": {
                "message": "Token is required",
                "details": "Please provide token as query parameter"
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Try Redis first (member invites)
    invite_data = RedisInviteManager.get_invite_by_token(token)
    
    if invite_data:
        # Redis invite found
        if RedisInviteManager.is_expired(invite_data):
            return Response({
                "success": False,
                "error": {
                    "message": "Invitation expired",
                    "details": "This invitation has expired. Please request a new one."
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "success": True,
            "email": invite_data['email'],
            "type": invite_data.get('type', 'member'),
            "tenant_id": invite_data.get('tenant_id'),
            "role": invite_data.get('role', 'developer')
        }, status=status.HTTP_200_OK)
    
    # Try database (tenant invites - legacy)
    invite, error_message = verify_token(token)
    
    if error_message:
        return Response({
            "success": False,
            "error": {
                "message": "Invalid or expired invitation",
                "details": error_message
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        "success": True,
        "email": invite.email,
        "type": "tenant"
    }, status=status.HTTP_200_OK)
