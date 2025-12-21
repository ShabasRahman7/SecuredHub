from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from drf_spectacular.utils import extend_schema, OpenApiTypes

from ..models import Tenant, TenantMember, User
from ..serializers.tenant import (
    TenantSerializer,
    TenantCreateSerializer,
    TenantUpdateSerializer,
    TenantMemberSerializer
)
from ..permissions import IsTenantOwner, IsTenantMember
from ..utils.redis_invites import RedisInviteManager
from ..utils.tenant_invites import send_member_invite_email


class TenantListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Tenants",
        responses={200: TenantSerializer(many=True)},
        tags=["Tenants"]
    )
    def get(self, request):
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




class MemberListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantMember]

    @extend_schema(
        summary="List Members",
        responses={200: TenantMemberSerializer(many=True)},
        tags=["Tenants"]
    )
    def get(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        include_deleted = request.query_params.get('include_deleted', 'false').lower() == 'true'

        if include_deleted:
            members = TenantMember.objects.filter(tenant=tenant).select_related('user')
        else:
            members = TenantMember.objects.filter(
                tenant=tenant,
                deleted_at__isnull=True
            ).select_related('user')
        serializer = TenantMemberSerializer(members, many=True)
        
        return Response(
            {
                "success": True,
                "count": members.count(),
                "members": serializer.data
            },
            status=status.HTTP_200_OK
        )


class MemberRemoveView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Remove Member",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Tenants"]
    )
    def delete(self, request, tenant_id, member_id):
        """
        Tenant owner delete member.

        - Default: soft delete (marks member as deleted, disables login, keeps data for 30 days).
        - With ?hard_delete=true: hard delete (permanently removes user and membership).
        """
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        hard_delete = request.query_params.get('hard_delete', 'false').lower() == 'true'

        member = get_object_or_404(TenantMember, id=member_id, tenant=tenant)
        
        if member.user == request.user:
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
        
        if hard_delete:
            user_email = member.user.email
            # Hard delete: permanently remove the underlying user account
            member.user.delete()

            return Response(
                {
                    "success": True,
                    "message": f"Member {user_email} permanently deleted"
                },
                status=status.HTTP_200_OK
            )

        # Soft delete: mark member as deleted and schedule hard delete
        member.soft_delete()

        return Response(
            {
                "success": True,
                "message": f"Member {member.user.email} deleted. Data will be permanently removed in 30 days.",
                "member": TenantMemberSerializer(member).data
            },
            status=status.HTTP_200_OK
        )


class MemberRestoreView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Restore Soft-Deleted Member",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Tenants"]
    )
    def post(self, request, tenant_id, member_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)

        member = get_object_or_404(
            TenantMember,
            id=member_id,
            tenant=tenant,
            deleted_at__isnull=False
        )

        member.restore()
        
        return Response(
            {
                "success": True,
                "message": f"Member {member.user.email} has been restored successfully",
                "member": TenantMemberSerializer(member).data
            },
            status=status.HTTP_200_OK
        )


class MemberBlockView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Block/Unblock Member",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Tenants"]
    )
    def post(self, request, tenant_id, member_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)

        member = get_object_or_404(TenantMember, id=member_id, tenant=tenant)
        block = request.data.get('block', True)

        # Owners cannot block themselves
        if member.user == request.user:
            return Response({
                "success": False,
                "error": {
                    "message": "Operation failed",
                    "details": "You cannot block yourself."
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        member.user.is_active = not block
        member.user.save(update_fields=['is_active'])

        return Response({
            "success": True,
            "message": f"Member {'blocked' if block else 'unblocked'} successfully"
        }, status=status.HTTP_200_OK)

class InviteDeveloperView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Invite Developer",
        request=OpenApiTypes.OBJECT,
        responses={201: OpenApiTypes.OBJECT},
        tags=["Tenants"]
    )
    def post(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
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
            # Do not allow inviting an account that already exists elsewhere
            return Response(
                {
                    "success": False,
                    "error": {
                        "message": "User already has an account",
                        "details": "This email is already registered. Ask them to request access from the tenant owner."
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
            invited_by_id=request.user.id,
            role='developer'
        )
        
        success, message = send_member_invite_email(
            email=email,
            tenant_name=tenant.name,
            invited_by_name=f"{request.user.first_name} {request.user.last_name}",
            token=invite_data['token']
        )
        
        return Response(
            {
                "success": True,
                "message": f"Invitation sent to {email}",
                "email_sent": success,
                "invite": invite_data
            },
            status=status.HTTP_201_CREATED
        )


class InviteListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="List Invites",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Tenants"]
    )
    def get(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        invites = RedisInviteManager.list_tenant_invites(tenant.id)
        
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


class ResendInviteView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Resend Invite",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Tenants"]
    )
    def post(self, request, tenant_id, invite_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
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
        
        RedisInviteManager.delete_invite(token)
        new_invite_data = RedisInviteManager.create_invite(
            tenant_id=tenant.id,
            email=invite_data['email'],
            invited_by_id=request.user.id,
            role=invite_data['role']
        )
        
        success, message = send_member_invite_email(
            email=new_invite_data['email'],
            tenant_name=tenant.name,
            invited_by_name=f"{request.user.first_name} {request.user.last_name}",
            token=new_invite_data['token']
        )
        
        if success:
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


class CancelInviteView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Cancel Invite",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Tenants"]
    )
    def delete(self, request, tenant_id, invite_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
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
        
        RedisInviteManager.delete_invite(token)
        
        return Response(
            {
                "success": True,
                "message": f"Invitation to {invite_data['email']} has been cancelled"
            },
            status=status.HTTP_200_OK
        )


class AcceptInviteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Accept Invite",
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        tags=["Tenants"]
    )
    def post(self, request):
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
        
        tenant = get_object_or_404(Tenant, id=invite_data['tenant_id'])
        
        try:
            TenantMember.objects.create(
                tenant=tenant,
                user=request.user,
                role=invite_data['role']
            )
            
            RedisInviteManager.delete_invite(token)
            
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


class TenantUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsTenantMember]

    @extend_schema(
        summary="Update Tenant",
        request=TenantUpdateSerializer,
        responses={200: TenantSerializer},
        tags=["Tenants"]
    )
    def put(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        serializer = TenantUpdateSerializer(tenant, data=request.data, partial=True)
        
        if not serializer.is_valid():
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
        
        serializer.save()
        return Response(
            {
                "success": True,
                "message": "Tenant updated successfully",
                "tenant": TenantSerializer(tenant, context={'request': request}).data
            },
            status=status.HTTP_200_OK
        )

    def patch(self, request, tenant_id):
        return self.put(request, tenant_id)


list_tenants = TenantListView.as_view()
update_tenant = TenantUpdateView.as_view()
list_members = MemberListView.as_view()
remove_member = MemberRemoveView.as_view()
restore_member = MemberRestoreView.as_view()
block_member = MemberBlockView.as_view()
invite_developer = InviteDeveloperView.as_view()
list_invites = InviteListView.as_view()
resend_invite = ResendInviteView.as_view()
cancel_invite = CancelInviteView.as_view()
accept_invite = AcceptInviteView.as_view()
