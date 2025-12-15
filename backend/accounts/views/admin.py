from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction, connection
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiTypes

from ..models import Tenant, TenantInvite, AccessRequest, TenantMember
from ..serializers import UserSerializer, AccessRequestSerializer
from ..serializers.tenant import TenantSerializer, TenantUpdateSerializer, TenantInviteSerializer
from ..permissions import IsAdmin
from ..utils.email import send_tenant_invite_email, send_access_request_rejection_email
from ..utils.redis_tokens import InviteTokenManager

User = get_user_model()


class AdminDeleteUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Admin Delete User",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Admin"]
    )
    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        
        if user.id == request.user.id:
            return Response({
                "success": False,
                "error": {
                    "message": "Cannot delete self",
                    "details": "You cannot delete your own account via this endpoint"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        return Response({
            "success": True,
            "message": "User deleted successfully"
        }, status=status.HTTP_200_OK)


class AdminUpdateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Admin Update User",
        request=UserSerializer,
        responses={200: UserSerializer},
        tags=["Admin"]
    )
    def put(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
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

    def patch(self, request, user_id):
        return self.put(request, user_id)


class AdminDeleteTenantView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Admin Delete Tenant (Soft Delete)",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Admin"]
    )
    def delete(self, request, tenant_id):
        """
        Soft delete a tenant. Data is retained for 30 days before permanent deletion.
        Use hard_delete parameter for immediate permanent deletion (use with caution).
        """
        hard_delete = request.query_params.get('hard_delete', 'false').lower() == 'true'
        
        if hard_delete:
            return self._hard_delete(request, tenant_id)
        else:
            return self._soft_delete(request, tenant_id)
    
    def _soft_delete(self, request, tenant_id):
        """Soft delete - marks tenant as deleted, keeps data for 30 days"""
        try:
            tenant = get_object_or_404(Tenant, id=tenant_id, deleted_at__isnull=True)
            
            # Soft delete the tenant
            tenant.soft_delete()
            
            return Response({
                "success": True,
                "message": f"Tenant '{tenant.name}' has been deleted. Data will be permanently removed in 30 days.",
                "tenant": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "deleted_at": tenant.deleted_at,
                    "deletion_scheduled_at": tenant.deletion_scheduled_at
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "error": {
                    "message": "Failed to delete tenant",
                    "details": str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _hard_delete(self, request, tenant_id):
        """Hard delete - permanently removes tenant and all data immediately"""
        try:
            with transaction.atomic():
                tenant = get_object_or_404(Tenant, id=tenant_id)
                
                # Store owner email before deletion
                owner_email = tenant.created_by.email if tenant.created_by else None
                
                # Check if users table has a tenant_id column and set it to NULL
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name='users' AND column_name='tenant_id'
                        """)
                        if cursor.fetchone():
                            cursor.execute("""
                                UPDATE users 
                                SET tenant_id = NULL 
                                WHERE tenant_id = %s
                            """, [tenant_id])
                except Exception:
                    pass
                
                # Delete all TenantMember records first and collect their users
                tenant_members = TenantMember.objects.filter(tenant=tenant)
                member_user_ids = list(tenant_members.values_list('user_id', flat=True))
                tenant_members.delete()
                
                # Delete member invites for this tenant
                from ..models import MemberInvite
                member_invites = MemberInvite.objects.filter(tenant=tenant)
                member_invites.delete()
                
                # Delete related tenant invites and access requests
                if owner_email:
                    tenant_invites = TenantInvite.objects.filter(email=owner_email)
                    for invite in tenant_invites:
                        try:
                            if invite.token:
                                InviteTokenManager.delete_token(str(invite.token))
                        except Exception:
                            pass
                    tenant_invites.delete()
                    
                    access_requests = AccessRequest.objects.filter(email=owner_email)
                    access_requests.delete()
                
                # Permanently delete the tenant
                tenant.delete()

                # Delete all non-staff, non-superuser users that belonged to this tenant
                if member_user_ids:
                    User.objects.filter(
                        id__in=member_user_ids,
                        is_staff=False,
                        is_superuser=False,
                    ).delete()
            
            return Response({
                "success": True,
                "message": "Tenant permanently deleted. All data has been removed."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "error": {
                    "message": "Failed to delete tenant",
                    "details": str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminUpdateTenantView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Admin Update Tenant",
        request=TenantUpdateSerializer,
        responses={200: TenantSerializer},
        tags=["Admin"]
    )
    def put(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        
        serializer = TenantUpdateSerializer(tenant, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
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

    def patch(self, request, tenant_id):
        return self.put(request, tenant_id)


class AdminBlockTenantView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Admin Block/Unblock Tenant",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Admin"]
    )
    def post(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        
        # Toggle is_active status
        tenant.is_active = not tenant.is_active
        tenant.save()
        
        action = "unblocked" if tenant.is_active else "blocked"
        
        return Response({
            "success": True,
            "message": f"Tenant {action} successfully",
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "is_active": tenant.is_active
            }
        }, status=status.HTTP_200_OK)


class AdminListTenantsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="List All Tenants (Admin)",
        responses={200: TenantSerializer(many=True)},
        tags=["Admin"]
    )
    def get(self, request):
        try:
            # By default, exclude soft-deleted tenants unless include_deleted=true
            include_deleted = request.query_params.get('include_deleted', 'false').lower() == 'true'
            
            if include_deleted:
                tenants = Tenant.objects.all().order_by('-created_at')
            else:
                # Check if deleted_at field exists by trying to query it
                # If migration hasn't been run, the field won't exist in DB
                try:
                    # Try a simple query to see if the field exists
                    # This will fail if the column doesn't exist
                    test_query = Tenant.objects.filter(deleted_at__isnull=True)[:1]
                    list(test_query)  # Force evaluation to check if field exists
                    tenants = Tenant.objects.filter(deleted_at__isnull=True).order_by('-created_at')
                except Exception:
                    # Field doesn't exist yet (migration not run), return all tenants
                    # This is a temporary workaround until migrations are run
                    tenants = Tenant.objects.all().order_by('-created_at')
            
            # Serialize tenants
            try:
                serializer = TenantSerializer(tenants, many=True, context={'request': request})
                tenants_data = serializer.data
            except Exception as serialize_error:
                # If serialization fails (e.g., due to missing fields), manually serialize
                tenants_data = []
                for tenant in tenants:
                    try:
                        tenant_data = TenantSerializer(tenant, context={'request': request}).data
                        tenants_data.append(tenant_data)
                    except Exception:
                        # Skip tenants that can't be serialized
                        continue
            
            return Response({
                "success": True,
                "count": len(tenants_data),
                "tenants": tenants_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            return Response({
                "success": False,
                "error": {
                    "message": "Failed to fetch tenants",
                    "details": str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminRestoreTenantView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Restore Soft-Deleted Tenant",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Admin"]
    )
    def post(self, request, tenant_id):
        """Restore a soft-deleted tenant"""
        try:
            tenant = get_object_or_404(Tenant, id=tenant_id, deleted_at__isnull=False)
            
            tenant.restore()
            
            return Response({
                "success": True,
                "message": f"Tenant '{tenant.name}' has been restored successfully",
                "tenant": TenantSerializer(tenant, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "error": {
                    "message": "Failed to restore tenant",
                    "details": str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminTenantInviteView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Admin Invite Tenant",
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        tags=["Admin"]
    )
    def post(self, request):
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
        
        if tenant_invite.status == TenantInvite.STATUS_EXPIRED or not created:
            tenant_invite.status = TenantInvite.STATUS_PENDING
            tenant_invite.invited_by = request.user
            
            if tenant_invite.token:
                InviteTokenManager.delete_token(str(tenant_invite.token))
            
            token = InviteTokenManager.create_token(email)
            tenant_invite.token = token
            tenant_invite.expires_at = timezone.now() + timedelta(hours=24)
            tenant_invite.save()
        
        success, message = send_tenant_invite_email(tenant_invite)
        
        if success:
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


class AdminTenantInviteListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="List Tenant Invites",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Admin"]
    )
    def get(self, request):
        invites = TenantInvite.objects.all().order_by('-invited_at')
        serializer = TenantInviteSerializer(invites, many=True)
        
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


class AdminResendTenantInviteView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Admin Resend Tenant Invite",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Admin"]
    )
    def post(self, request, invite_id):
        invite = get_object_or_404(TenantInvite, id=invite_id)
        
        if invite.status == TenantInvite.STATUS_REGISTERED:
            return Response({
                "success": False,
                "error": {
                    "message": "Cannot resend",
                    "details": "This invitation has already been registered."
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if invite.token:
            InviteTokenManager.delete_token(str(invite.token))
        
        token = InviteTokenManager.create_token(invite.email)
        invite.token = token
        invite.expires_at = timezone.now() + timedelta(hours=24)
        invite.status = TenantInvite.STATUS_PENDING
        invite.save()
        
        success, message = send_tenant_invite_email(invite)
        
        if success:
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


class AdminDeleteTenantInviteView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Admin Delete Tenant Invite",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Admin"]
    )
    def delete(self, request, invite_id):
        invite = get_object_or_404(TenantInvite, id=invite_id)
        
        email = invite.email
        invite.delete()
        
        return Response({
            "success": True,
            "message": f"Invitation for {email} has been deleted."
        }, status=status.HTTP_200_OK)


class AdminAccessRequestListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="List Access Requests",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Admin"]
    )
    def get(self, request):
        try:
            requests = AccessRequest.objects.all().order_by('-created_at')
            serializer = AccessRequestSerializer(requests, many=True)
            
            return Response({
                "success": True,
                "count": requests.count(),
                "results": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "error": {
                    "message": "Failed to fetch access requests",
                    "details": str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminApproveAccessRequestView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Approve Access Request",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Admin"]
    )
    def post(self, request, request_id):
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
            
        if tenant_invite.token:
            InviteTokenManager.delete_token(str(tenant_invite.token))
        
        token = InviteTokenManager.create_token(access_request.email)
        tenant_invite.token = token
        tenant_invite.expires_at = timezone.now() + timedelta(hours=24)
        tenant_invite.status = TenantInvite.STATUS_PENDING
        tenant_invite.invited_by = request.user
        tenant_invite.save()
        
        success, message = send_tenant_invite_email(tenant_invite)
        
        if success:
            access_request.status = AccessRequest.STATUS_APPROVED
            access_request.save()
            
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


class AdminRejectAccessRequestView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Reject Access Request",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Admin"]
    )
    def post(self, request, request_id):
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
        
        send_access_request_rejection_email(access_request.email)
        
        return Response({
            "success": True,
            "message": f"Access request for {access_request.email} rejected."
        }, status=status.HTTP_200_OK)


class AdminDeleteAccessRequestView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Delete Access Request",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Admin"]
    )
    def delete(self, request, request_id):
        access_request = get_object_or_404(AccessRequest, id=request_id)
        email = access_request.email
        
        tenant_invites = TenantInvite.objects.filter(email=email)
        for invite in tenant_invites:
            if invite.token:
                InviteTokenManager.delete_token(str(invite.token))
        tenant_invites.delete()
        
        access_request.delete()
        
        return Response({
            "success": True,
            "message": f"Access request for {email} has been deleted."
        }, status=status.HTTP_200_OK)


admin_delete_user = AdminDeleteUserView.as_view()
admin_update_user = AdminUpdateUserView.as_view()
admin_delete_tenant = AdminDeleteTenantView.as_view()
admin_update_tenant = AdminUpdateTenantView.as_view()
admin_block_tenant = AdminBlockTenantView.as_view()
admin_restore_tenant = AdminRestoreTenantView.as_view()
admin_list_tenants = AdminListTenantsView.as_view()
admin_invite_tenant = AdminTenantInviteView.as_view()
list_tenant_invites = AdminTenantInviteListView.as_view()
admin_resend_tenant_invite = AdminResendTenantInviteView.as_view()
admin_delete_tenant_invite = AdminDeleteTenantInviteView.as_view()
admin_list_access_requests = AdminAccessRequestListView.as_view()
admin_approve_access_request = AdminApproveAccessRequestView.as_view()
admin_reject_access_request = AdminRejectAccessRequestView.as_view()
admin_delete_access_request = AdminDeleteAccessRequestView.as_view()
