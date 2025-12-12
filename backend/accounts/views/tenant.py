"""
Tenant (Tenant) management views.
"""
from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.utils import timezone

from ..models import Tenant, TenantMember, TenantInvite, User
from ..serializers.tenant import (
    TenantSerializer,
    TenantCreateSerializer,
    TenantUpdateSerializer,
    TenantMemberSerializer,
    InviteCreateSerializer,
    InviteSerializer,
    AcceptInviteSerializer
)
from ..utils import user_has_tenant_access, user_is_tenant_owner
from ..utils.redis_invites import RedisInviteManager

import logging
import uuid

logger = logging.getLogger('api')


# --- Tenant Management ---

@extend_schema(
    summary="List Tenants",
    description="List all tenants the current user is a member of.",
    responses={200: TenantSerializer(many=True)},
    tags=["Tenants"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tenants(request):
    """
    List all tenants the current user is a member of.
    
    GET /api/v1/tenants/
    """
    user = request.user
    
    memberships = TenantMember.objects.filter(user=user).select_related('tenant')
    tenants = [m.tenant for m in memberships]
    
    serializer = TenantSerializer(tenants, many=True, context={'request': request})
    
    return Response(
        {
            "success": True,
            "count": len(tenants),
            "tenants": serializer.data
        },
        status=status.HTTP_200_OK
    )


@extend_schema(
    summary="Create Tenant",
    description="Create a new tenant.",
    request=TenantCreateSerializer,
    responses={201: TenantSerializer},
    tags=["Tenants"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_tenant(request):
    """
    Create a new tenant.
    
    POST /api/v1/tenants/create/
    Body: {
        "name": "My Tenant",
        "description": "Optional description"
    }
    """
    serializer = TenantCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        try:
            tenant = serializer.save()
            logger.info(f"Tenant '{tenant.name}' created by user {request.user.id}")
            
            return Response(
                {
                    "success": True,
                    "message": "Tenant created successfully",
                    "tenant": TenantSerializer(tenant, context={'request': request}).data
                },
                status=status.HTTP_201_CREATED
            )
        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "error": {
                        "message": "Tenant creation failed",
                        "details": "A tenant with this name may already exist."
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(
        {
            "success": False,
            "error": {
                "message": "Validation failed",
                "details": serializer.errors
            }
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@extend_schema(
    summary="Get Tenant Details",
    description="Get details of a specific tenant.",
    responses={200: TenantSerializer},
    tags=["Tenants"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tenant(request, tenant_id):
    """
    Get details of a specific tenant.
    
    GET /api/v1/tenants/{tenant_id}/
    """
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if not user_has_tenant_access(user, tenant):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "You are not a member of this tenant."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = TenantSerializer(tenant, context={'request': request})
    
    return Response(
        {
            "success": True,
            "tenant": serializer.data
        },
        status=status.HTTP_200_OK
    )


@extend_schema(
    summary="Update Tenant",
    description="Update tenant details (owner only).",
    request=TenantUpdateSerializer,
    responses={200: TenantSerializer},
    tags=["Tenants"]
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_tenant(request, tenant_id):
    """
    Update tenant details (owner only).
    
    PUT/PATCH /api/v1/tenants/{tenant_id}/update/
    """
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if not user_is_tenant_owner(user, tenant):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "Only the owner can update tenant details."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = TenantUpdateSerializer(tenant, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        logger.info(f"Tenant {tenant_id} updated by user {user.id}")
        
        return Response(
            {
                "success": True,
                "message": "Tenant updated successfully",
                "tenant": TenantSerializer(tenant, context={'request': request}).data
            },
            status=status.HTTP_200_OK
        )
    
    return Response(
        {
            "success": False,
            "error": {
                "message": "Validation failed",
                "details": serializer.errors
            }
        },
        status=status.HTTP_400_BAD_REQUEST
    )


# --- Member Management ---

@extend_schema(
    summary="List Members",
    description="List all members of a tenant.",
    responses={200: TenantMemberSerializer(many=True)},
    tags=["Tenants"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_members(request, tenant_id):
    """
    List all members of a tenant.
    
    GET /api/v1/tenants/{tenant_id}/members/
    """
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if not user_has_tenant_access(user, tenant):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "You are not a member of this tenant."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    members = TenantMember.objects.filter(tenant=tenant).select_related('user')
    serializer = TenantMemberSerializer(members, many=True)
    
    return Response(
        {
            "success": True,
            "count": members.count(),
            "members": serializer.data
        },
        status=status.HTTP_200_OK
    )


@extend_schema(
    summary="Remove Member",
    description="Remove a member from the tenant (owner only).",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Tenants"]
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_member(request, tenant_id, member_id):
    """
    Remove a member from the tenant (owner only).
    
    DELETE /api/v1/tenants/{tenant_id}/members/{member_id}/remove/
    """
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if not user_is_tenant_owner(user, tenant):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "Only the owner can remove members."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    member_to_remove = get_object_or_404(TenantMember, id=member_id, tenant=tenant)
    
    # Prevent removing self (owner)
    if member_to_remove.user == user:
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Operation failed",
                    "details": "You cannot remove yourself from the tenant."
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user_email = member_to_remove.user.email
    member_to_remove.delete()
    logger.info(f"Member {user_email} removed from tenant {tenant_id} by {user.id}")
    
    return Response(
        {
            "success": True,
            "message": f"Member {user_email} removed successfully"
        },
        status=status.HTTP_200_OK
    )


# --- Invitation Management ---

@extend_schema(
    summary="Invite Developer",
    description="Invite a developer to the tenant (owner only).",
    request=InviteCreateSerializer,
    responses={201: InviteSerializer},
    tags=["Tenants"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invite_developer(request, tenant_id):
    """
    Invite a developer to the tenant (Redis-based).
    
    POST /api/v1/tenants/{tenant_id}/invite/
    Body: { "email": "dev@example.com" }
    """
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if not user_is_tenant_owner(user, tenant):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "Only the owner can invite members."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    email = request.data.get('email')
    if not email:
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Validation failed",
                    "details": {"email": ["This field is required."]}
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(email=email).exists():
        existing_user = User.objects.get(email=email)
        if TenantMember.objects.filter(tenant=tenant, user=existing_user).exists():
            return Response(
                {
                    "success": False,
                    "error": {
                        "message": "User is already a member",
                        "details": "This user is already a member of this tenant."
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    existing_invite = RedisInviteManager.get_invite_by_email(tenant.id, email)
    if existing_invite and not RedisInviteManager.is_expired(existing_invite):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Active invitation exists",
                    "details": "An active invitation already exists for this email."
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    invite_data = RedisInviteManager.create_invite(
        tenant_id=tenant.id,
        email=email,
        invited_by_id=user.id,
        role='developer'
    )
    
    from ..utils.tenant_invites import send_member_invite_email
    success, message = send_member_invite_email(
        email=email,
        tenant_name=tenant.name,
        invited_by_name=f"{user.first_name} {user.last_name}",
        token=invite_data['token']
    )
    
    if not success:
        logger.warning(f"Invite created but email failed for {email}: {message}")
    
    logger.info(f"Invite created for {email} in tenant {tenant_id}")
    
    return Response(
        {
            "success": True,
            "message": f"Invitation sent to {email}",
            "email_sent": success,
            "invite": invite_data
        },
        status=status.HTTP_201_CREATED
    )


@extend_schema(
    summary="List Invites",
    description="List all pending invitations for a tenant.",
    responses={200: InviteSerializer(many=True)},
    tags=["Tenants"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_invites(request, tenant_id):
    """List all pending invitations for a tenant (Redis-based)."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if not user_is_tenant_owner(user, tenant):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "Only the owner can view invites."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get invites from Redis
    invites = RedisInviteManager.list_tenant_invites(tenant.id)
    
    # Add is_expired flag to each invite
    for invite in invites:
        invite['is_expired'] = RedisInviteManager.is_expired(invite)
    
    return Response(
        {
            "success": True,
            "count": len(invites),
            "invites": invites
        },
        status=status.HTTP_200_OK
    )


@extend_schema(
    summary="Resend Invite",
    description="Resend an invitation email (with cooldown).",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Tenants"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_invite(request, tenant_id, invite_id):
    """Resend an invitation email (Redis-based). invite_id is actually the token."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if not user_is_tenant_owner(user, tenant):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "Only the owner can resend invites."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get invite from Redis (invite_id is the token)
    token = invite_id
    invite_data = RedisInviteManager.get_invite_by_token(token)
    
    if not invite_data:
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Invite not found",
                    "details": "This invitation has expired or been cancelled."
                }
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verify tenant matches
    if invite_data['tenant_id'] != tenant.id:
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "This invite belongs to a different tenant."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Delete old invite and create new one with fresh token
    RedisInviteManager.delete_invite(token)
    new_invite_data = RedisInviteManager.create_invite(
        tenant_id=tenant.id,
        email=invite_data['email'],
        invited_by_id=user.id,
        role=invite_data['role']
    )
    
    # Send invitation email with new token
    from ..utils.tenant_invites import send_member_invite_email
    success, message = send_member_invite_email(
        email=new_invite_data['email'],
        tenant_name=tenant.name,
        invited_by_name=f"{user.first_name} {user.last_name}",
        token=new_invite_data['token']
    )
    
    if success:
        logger.info(f"Invite resent to {new_invite_data['email']} by {user.email}")
        return Response(
            {
                "success": True,
                "message": f"Invitation resent to {new_invite_data['email']}",
                "invite": new_invite_data
            },
            status=status.HTTP_200_OK
        )
    else:
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Failed to resend invitation",
                    "details": message
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Cancel Invite",
    description="Cancel a pending invitation.",
    responses={200: OpenApiTypes.OBJECT},
    tags=["Tenants"]
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancel_invite(request, tenant_id, invite_id):
    """Cancel a pending invitation (Redis-based). invite_id is actually the token."""
    user = request.user
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if not user_is_tenant_owner(user, tenant):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "Only the owner can cancel invites."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get invite from Redis (invite_id is the token)
    token = invite_id
    invite_data = RedisInviteManager.get_invite_by_token(token)
    
    if not invite_data:
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Invite not found",
                    "details": "This invitation has expired or been cancelled."
                }
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verify tenant matches
    if invite_data['tenant_id'] != tenant.id:
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Unauthorized",
                    "details": "This invite belongs to a different tenant."
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Delete invite from Redis
    RedisInviteManager.delete_invite(token)
    
    logger.info(f"Invite cancelled for {invite_data['email']} by {user.email}")
    
    return Response(
        {
            "success": True,
            "message": f"Invitation to {invite_data['email']} has been cancelled"
        },
        status=status.HTTP_200_OK
    )


@extend_schema(
    summary="Accept Invite",
    description="Accept an invitation to join a tenant.",
    request=AcceptInviteSerializer,
    responses={200: OpenApiTypes.OBJECT},
    tags=["Tenants"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_invite(request):
    """Accept an invitation to join a tenant (Redis-based)."""
    token = request.data.get('token')
    
    if not token:
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Token required",
                    "details": "Please provide an invitation token."
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get invite from Redis
    invite_data = RedisInviteManager.get_invite_by_token(token, invite_type='member')
    
    if not invite_data:
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Invalid invitation",
                    "details": "This invitation has expired or been cancelled."
                }
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if expired
    if RedisInviteManager.is_expired(invite_data):
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Invitation expired",
                    "details": "This invitation has expired. Please request a new one."
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user email matches invite email
    if invite_data['email'] != request.user.email:
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Invalid invitation",
                    "details": "This invitation was sent to a different email address."
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get tenant
    tenant = get_object_or_404(Tenant, id=invite_data['tenant_id'])
    
    # Add user to tenant
    try:
        TenantMember.objects.create(
            tenant=tenant,
            user=request.user,
            role=invite_data['role']
        )
        
        # Delete invite from Redis (mark as accepted)
        RedisInviteManager.delete_invite(token)
        
        logger.info(f"User {request.user.email} accepted invite to {tenant.name}")
        
        return Response(
            {
                "success": True,
                "message": f"Successfully joined {tenant.name}",
                "tenant": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "role": invite_data['role']
                }
            },
            status=status.HTTP_200_OK
        )
    except IntegrityError:
        return Response(
            {
                "success": False,
                "error": {
                    "message": "Operation failed",
                    "details": "You are already a member of this tenant."
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response(
        {
            "success": False,
            "error": {
                "message": "Validation failed",
                "details": serializer.errors
            }
        },
        status=status.HTTP_400_BAD_REQUEST
    )


