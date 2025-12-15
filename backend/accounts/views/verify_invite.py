from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiTypes

from ..utils.email import verify_tenant_invite_token as verify_tenant_invite_token_util
from ..utils.redis_invites import RedisInviteManager


class VerifyTenantInviteTokenView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify Tenant Invite Token",
        request={"application/json": {"token": "string"}},
        responses={200: OpenApiTypes.OBJECT},
        tags=["Authentication"]
    )
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response({
                "success": False,
                "error": {
                    "message": "Token is required",
                    "details": "Please provide an invitation token"
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        invite, error_message = verify_tenant_invite_token(token)
        
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


class VerifyInviteTokenGetView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify Invite Token (GET)",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Authentication"]
    )
    def get(self, request):
        try:
            token = request.GET.get('token')
            
            if not token:
                return Response({
                    "success": False,
                    "error": {
                        "message": "Token is required",
                        "details": "Please provide token as query parameter"
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            invite_data = RedisInviteManager.get_invite_by_token(token)
            
            if invite_data:
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
                    "email": invite_data.get('email'),
                    "type": invite_data.get('type', 'member'),
                    "tenant_id": invite_data.get('tenant_id'),
                    "role": invite_data.get('role', 'developer')
                }, status=status.HTTP_200_OK)
            
            invite, error_message = verify_tenant_invite_token_util(token)
            
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
        except Exception as e:
            import traceback
            trace = traceback.format_exc()
            # Surface the actual error for easier debugging (especially when cache/redis is down)
            return Response({
                "success": False,
                "error": {
                    "message": "Invite verification failed",
                    "details": str(e),
                    "trace": trace
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


verify_tenant_invite_token_view = VerifyTenantInviteTokenView.as_view()
verify_invite_token_get = VerifyInviteTokenGetView.as_view()
