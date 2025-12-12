from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from ..models import Tenant, TenantInvite
from ..serializers import UserSerializer
from ..serializers.tenant import TenantSerializer, TenantUpdateSerializer
from drf_spectacular.utils import extend_schema, OpenApiTypes
import logging

logger = logging.getLogger('api')
User = get_user_model()

# --- Admin User Management ---

@extend_schema(
    summary="Admin Delete User",
    description="Delete a user account (admin only).",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Admin"]
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_delete_user(request, user_id):
    """
    Delete a user account (admin only).
    
    DELETE /api/v1/auth/admin/users/{user_id}/
    """
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting self
    if user.id == request.user.id:
        return Response({
            "success": False,
            "error": {
                "message": "Cannot delete self",
                "details": "You cannot delete your own account via this endpoint"
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    user.delete()
    logger.info(f"User deleted by admin: {user.email} deleted by {request.user.email}")
    
    return Response({
        "success": True,
        "message": "User deleted successfully"
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Admin Update User",
    description="Update a user account (admin only).",
    request=UserSerializer,
    responses={200: UserSerializer},
    tags=["Admin"]
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_update_user(request, user_id):
    """
    Update a user account (admin only).
    
    PUT/PATCH /api/v1/auth/admin/users/{user_id}/
    """
    user = get_object_or_404(User, id=user_id)
    
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        logger.info(f"User updated by admin: {user.email} updated by {request.user.email}")
        
        return Response({
            "success": True,
            "message": "User updated successfully",
            "user": serializer.data
        }, status=status.HTTP_200_OK)
        
    return Response({
        "success": False,
        "error": {
            "message": "Failed to update user",
            "details": serializer.errors
        }
    }, status=status.HTTP_400_BAD_REQUEST)


# --- Admin Tenant Management ---

@extend_schema(
    summary="Admin Delete Tenant",
    description="Delete a tenant (admin only).",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Admin"]
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_delete_tenant(request, tenant_id):
    """
    Delete a tenant (admin only).
    
    DELETE /api/v1/auth/admin/tenants/{tenant_id}/
    """
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    # Get owner email before deleting tenant
    owner_email = tenant.created_by.email
    tenant_name = tenant.name
    
    logger.info(f"[CASCADE DELETE] Starting tenant deletion for: {tenant_name} (owner: {owner_email})")
    
    # Delete tenant (this will cascade delete TenantMembers)
    tenant.delete()
    logger.info(f"[CASCADE DELETE] Tenant {tenant_name} deleted from database")
    
    # Clean up orphaned AccessRequest and TenantInvite records
    # This allows the email to request access again if needed
    from ..models import AccessRequest, TenantInvite
    from ..utils.redis_tokens import InviteTokenManager
    
    # Delete associated TenantInvite
    tenant_invites = TenantInvite.objects.filter(email=owner_email)
    invite_count = tenant_invites.count()
    logger.info(f"[CASCADE DELETE] Found {invite_count} TenantInvite(s) for {owner_email}")
    
    for invite in tenant_invites:
        # Delete token from Redis if exists
        if invite.token:
            InviteTokenManager.delete_token(str(invite.token))
            logger.info(f"[CASCADE DELETE] Deleted Redis token: {str(invite.token)[:8]}...")
    tenant_invites.delete()
    logger.info(f"[CASCADE DELETE] Deleted {invite_count} TenantInvite(s)")
    
    # Delete associated AccessRequest
    access_requests = AccessRequest.objects.filter(email=owner_email)
    ar_count = access_requests.count()
    logger.info(f"[CASCADE DELETE] Found {ar_count} AccessRequest(s) for {owner_email}")
    access_requests.delete()
    logger.info(f"[CASCADE DELETE] Deleted {ar_count} AccessRequest(s)")
    
    logger.info(f"[CASCADE DELETE] Cleanup complete for {owner_email}")
    
    return Response({
        "success": True,
        "message": "Tenant deleted successfully"
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Admin Update Tenant",
    description="Update a tenant (admin only).",
    request=TenantUpdateSerializer,
    responses={200: TenantSerializer},
    tags=["Admin"]
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_update_tenant(request, tenant_id):
    """
    Update a tenant (admin only).
    
    PUT/PATCH /api/v1/auth/admin/tenants/{tenant_id}/
    """
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    serializer = TenantUpdateSerializer(tenant, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        logger.info(f"Tenant updated by admin: {tenant.name} updated by {request.user.email}")
        
        return Response({
            "success": True,
            "message": "Tenant updated successfully",
            "tenant": TenantSerializer(tenant, context={'request': request}).data
        }, status=status.HTTP_200_OK)
        
    return Response({
        "success": False,
        "error": {
            "message": "Failed to update tenant",
            "details": serializer.errors
        }
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="List All Tenants (Admin)",
    description="List all tenants (admin only).",
    responses={200: TenantSerializer(many=True)},
    tags=["Admin"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_list_tenants(request):
    """List all tenants (admin only)."""
    if not request.user.is_superuser:
        return Response({
            "success": False,
            "error": {
                "message": "Permission denied",
                "details": "Only administrators can view all tenants"
            }
        }, status=status.HTTP_403_FORBIDDEN)

    tenants = Tenant.objects.all().order_by('-created_at')
    
    serializer = TenantSerializer(tenants, many=True, context={'request': request})
    
    return Response({
        "success": True,
        "count": tenants.count(),
        "tenants": serializer.data
    }, status=status.HTTP_200_OK)


# --- Admin Tenant Invitation ---

@extend_schema(
    summary="Admin Invite Tenant",
    description="Send an email invite for tenant registration (admin only).",
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT},
    tags=["Admin"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_invite_tenant(request):
    """
    Send an email invite for tenant registration (admin only).
    
    POST /api/v1/auth/admin/invite-tenant/
    Body: { "email": "tenant@example.com" }
    """
    email = request.data.get('email')
    
    if not email:
        return Response({
            "success": False,
            "error": {
                "message": "Email is required",
                "details": "Please provide an email address"
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=email).exists():
        return Response({
            "success": False,
            "error": {
                "message": "User already exists",
                "details": "A user with this email address already has an account"
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create or update TenantInvite record
    from ..models import TenantInvite
    from ..utils.email import send_tenant_invite_email
    from ..utils.redis_tokens import InviteTokenManager
    
    tenant_invite, created = TenantInvite.objects.get_or_create(
        email=email,
        defaults={'invited_by': request.user}
    )
    
    if not created and tenant_invite.status == TenantInvite.STATUS_REGISTERED:
        return Response({
            "success": False,
            "error": {
                "message": "User already registered",
                "details": "This email has already been used to register a tenant account"
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Reset to pending if it was expired or regenerate token
    if tenant_invite.status == TenantInvite.STATUS_EXPIRED or not created:
        tenant_invite.status = TenantInvite.STATUS_PENDING
        tenant_invite.invited_by = request.user
        
        # Delete old token from Redis if exists
        if tenant_invite.token:
            InviteTokenManager.delete_token(str(tenant_invite.token))
        
        # Create new token in Redis with 24h TTL
        from django.utils import timezone
        from datetime import timedelta
        token = InviteTokenManager.create_token(email)
        tenant_invite.token = token
        tenant_invite.expires_at = timezone.now() + timedelta(hours=24)
        tenant_invite.save()
    
    # Send invitation email with signup link
    success, message = send_tenant_invite_email(tenant_invite)
    
    if success:
        logger.info(f"Admin {request.user.email} sent tenant invite to {email}")
        return Response({
            "success": True,
            "message": f"Tenant invitation sent to {email}. They have 24 hours to register."
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "success": False,
            "error": {
                "message": "Failed to send invite",
                "details": message
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="List Tenant Invites",
    description="List all tenant invitations (admin only).",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Admin"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def list_tenant_invites(request):
    """
    List all tenant invitations - both registered and pending (admin only).
    
    GET /api/v1/auth/admin/tenant-invites/
    """
    from ..serializers.invite import TenantInviteSerializer
    
    invites = TenantInvite.objects.all().order_by('-invited_at')
    serializer = TenantInviteSerializer(invites, many=True)
    
    # Separate into verified and unverified
    verified = [inv for inv in serializer.data if inv['status'] == 'registered']
    unverified = [inv for inv in serializer.data if inv['status'] == 'pending']
    
    return Response({
        "success": True,
        "total": invites.count(),
        "verified_count": len(verified),
        "unverified_count": len(unverified),
        "verified": verified,
        "unverified": unverified,
        "all_invites": serializer.data
    }, status=status.HTTP_200_OK)



@extend_schema(
    summary="Admin Resend Tenant Invite",
    description="Resend a tenant invitation email (admin only).",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Admin"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_resend_tenant_invite(request, invite_id):
    """
    Resend a tenant invitation email (admin only).
    
    POST /api/v1/auth/admin/tenant-invites/{invite_id}/resend/
    """
    from ..models import TenantInvite
    from ..utils.email import send_tenant_invite_email
    
    invite = get_object_or_404(TenantInvite, id=invite_id)
    
    if invite.status == TenantInvite.STATUS_REGISTERED:
        return Response({
            "success": False,
            "error": {
                "message": "Cannot resend",
                "details": "This invitation has already been registered."
            }
        }, status=status.HTTP_400_BAD_REQUEST)
        
    # Regenerate token and expiry
    from ..utils.redis_tokens import InviteTokenManager
    from django.utils import timezone
    from datetime import timedelta
    
    # Delete old token from Redis
    if invite.token:
        InviteTokenManager.delete_token(str(invite.token))
    
    # Create new token in Redis with 24h TTL
    token = InviteTokenManager.create_token(invite.email)
    invite.token = token
    invite.expires_at = timezone.now() + timedelta(hours=24)
    invite.status = TenantInvite.STATUS_PENDING # Ensure it's pending
    invite.save()
    
    success, message = send_tenant_invite_email(invite)
    
    if success:
        logger.info(f"Admin {request.user.email} resent tenant invite to {invite.email}")
        return Response({
            "success": True,
            "message": f"Invitation resent to {invite.email}"
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "success": False,
            "error": {
                "message": "Failed to send invite",
                "details": message
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Admin Delete Tenant Invite",
    description="Delete/Cancel a tenant invitation (admin only).",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Admin"]
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_delete_tenant_invite(request, invite_id):
    """
    Delete/Cancel a tenant invitation (admin only).
    
    DELETE /api/v1/auth/admin/tenant-invites/{invite_id}/delete/
    """
    from ..models import TenantInvite
    
    invite = get_object_or_404(TenantInvite, id=invite_id)
    
    email = invite.email
    invite.delete()
    logger.info(f"Admin {request.user.email} deleted tenant invite for {email}")
    
    return Response({
        "success": True,
        "message": f"Invitation for {email} has been deleted."
    }, status=status.HTTP_200_OK)


# --- Admin Access Request Management ---

@extend_schema(
    summary="List Access Requests",
    description="List all access requests (admin only).",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Admin"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_list_access_requests(request):
    """
    List all access requests (admin only).
    
    GET /api/v1/auth/admin/access-requests/
    """
    from ..models import AccessRequest
    from ..serializers.access_request import AccessRequestSerializer
    
    requests = AccessRequest.objects.all().order_by('-created_at')
    serializer = AccessRequestSerializer(requests, many=True)
    
    return Response({
        "success": True,
        "count": requests.count(),
        "results": serializer.data
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Approve Access Request",
    description="Approve an access request and send invite (admin only).",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Admin"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_approve_access_request(request, request_id):
    """
    Approve an access request (admin only).
    
    POST /api/v1/auth/admin/access-requests/{request_id}/approve/
    """
    from ..models import AccessRequest, TenantInvite
    from ..utils.email import send_tenant_invite_email
    import uuid
    from django.utils import timezone
    from datetime import timedelta
    
    access_request = get_object_or_404(AccessRequest, id=request_id)
    
    if access_request.status == AccessRequest.STATUS_APPROVED:
        return Response({
            "success": False,
            "error": {
                "message": "Already approved",
                "details": "This request has already been approved."
            }
        }, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(email=access_request.email).exists():
        return Response({
            "success": False,
            "error": {
                "message": "User already exists",
                "details": "A user with this email address already has an account"
            }
        }, status=status.HTTP_400_BAD_REQUEST)
        
    # Create TenantInvite
    tenant_invite, created = TenantInvite.objects.get_or_create(
        email=access_request.email,
        defaults={'invited_by': request.user}
    )
    
    if not created and tenant_invite.status == TenantInvite.STATUS_REGISTERED:
        return Response({
            "success": False,
            "error": {
                "message": "User already registered",
                "details": "This email has already been used to register a tenant account"
            }
        }, status=status.HTTP_400_BAD_REQUEST)
        
    # Update Invite Token
    from ..utils.redis_tokens import InviteTokenManager
    
    # Delete old token from Redis if exists
    if tenant_invite.token:
        InviteTokenManager.delete_token(str(tenant_invite.token))
    
    # Create new token in Redis with 24h TTL
    token = InviteTokenManager.create_token(access_request.email)
    tenant_invite.token = token
    tenant_invite.expires_at = timezone.now() + timedelta(hours=24)
    tenant_invite.status = TenantInvite.STATUS_PENDING
    tenant_invite.invited_by = request.user
    tenant_invite.save()
    
    # Send Email
    success, message = send_tenant_invite_email(tenant_invite)
    
    if success:
        access_request.status = AccessRequest.STATUS_APPROVED
        access_request.save()
        logger.info(f"Admin {request.user.email} approved access request for {access_request.email}")
        
        return Response({
            "success": True,
            "message": f"Access request approved. Invite sent to {access_request.email}"
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "success": False,
            "error": {
                "message": "Failed to send invite",
                "details": message
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Reject Access Request",
    description="Reject an access request (admin only).",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Admin"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_reject_access_request(request, request_id):
    """
    Reject an access request (admin only).
    
    POST /api/v1/auth/admin/access-requests/{request_id}/reject/
    """
    from ..models import AccessRequest
    
    access_request = get_object_or_404(AccessRequest, id=request_id)
    
    if access_request.status == AccessRequest.STATUS_REJECTED:
        return Response({
            "success": False,
            "error": {
                "message": "Already rejected",
                "details": "This request has already been rejected."
            }
        }, status=status.HTTP_400_BAD_REQUEST)
        
    access_request.status = AccessRequest.STATUS_REJECTED
    access_request.save()
    
    # Send Rejection Email
    from ..utils.email import send_access_request_rejection_email
    send_access_request_rejection_email(access_request.email)
    
    logger.info(f"Admin {request.user.email} rejected access request for {access_request.email}")
    
    return Response({
        "success": True,
        "message": f"Access request for {access_request.email} rejected."
    }, status=status.HTTP_200_OK)

@extend_schema(
    summary="Delete Access Request",
    description="Delete an access request and associated TenantInvite (admin only).",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Admin"]
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_delete_access_request(request, request_id):
    """
    Delete an access request (admin only).
    Also deletes associated TenantInvite if exists.
    
    DELETE /api/v1/auth/admin/access-requests/{request_id}/delete/
    """
    from ..models import AccessRequest, TenantInvite
    from ..utils.redis_tokens import InviteTokenManager
    
    access_request = get_object_or_404(AccessRequest, id=request_id)
    email = access_request.email
    
    # Delete associated TenantInvite if exists
    tenant_invites = TenantInvite.objects.filter(email=email)
    for invite in tenant_invites:
        # Delete token from Redis if exists
        if invite.token:
            InviteTokenManager.delete_token(str(invite.token))
            logger.info(f"Deleted Redis token for {email}")
    tenant_invites.delete()
    
    # Delete the access request
    access_request.delete()
    
    logger.info(f"Admin {request.user.email} deleted access request for {email}")
    
    return Response({
        "success": True,
        "message": f"Access request for {email} has been deleted."
    }, status=status.HTTP_200_OK)
