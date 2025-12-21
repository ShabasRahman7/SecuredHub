from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiTypes

from ..serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    SendOTPSerializer, VerifyOTPSerializer, ResetPasswordSerializer,
    AccessRequestSerializer
)
from ..models import TenantInvite, TenantMember, Tenant, AccessRequest
from ..utils.otp import send_otp_email, verify_otp_code
from ..utils.redis_invites import RedisInviteManager
from ..utils.email import verify_tenant_invite_token

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register a new user (Invite-Only)",
        request=RegisterSerializer,
        responses={201: RegisterSerializer},
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": {"message": "Registration failed", "details": serializer.errors}
            }, status=status.HTTP_400_BAD_REQUEST)

        invite_token = request.data.get('invite_token')
        email = serializer.validated_data['email']
        
        validated_invite, is_tenant_signup, error_response = self._validate_invite(invite_token, email)
        if error_response:
            return error_response
        
        user = serializer.save()
        self._process_membership(user, validated_invite, is_tenant_signup, invite_token)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            "success": True,
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.get_role(),
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_201_CREATED)

    def _validate_invite(self, invite_token, email):
        if invite_token:
            invite_data = RedisInviteManager.get_invite_by_token(invite_token)
            if invite_data:
                if RedisInviteManager.is_expired(invite_data):
                    return None, None, Response({
                        "success": False,
                        "error": {"message": "Invitation expired. Please request a new one."}
                    }, status=status.HTTP_400_BAD_REQUEST)
                if invite_data['email'] != email:
                    return None, None, Response({
                        "success": False,
                        "error": {"message": "Email doesn't match invitation"}
                    }, status=status.HTTP_400_BAD_REQUEST)
                return invite_data, (invite_data.get('type') == 'tenant'), None
            else:
                tenant_invite, error = verify_tenant_invite_token(invite_token)
                if error or not tenant_invite or tenant_invite.email != email:
                    return None, None, Response({
                        "success": False,
                        "error": {"message": "Invalid or expired invitation"}
                    }, status=status.HTTP_400_BAD_REQUEST)
                return tenant_invite, True, None
        else:
            try:
                tenant_invite = TenantInvite.objects.get(
                    email=email, status=TenantInvite.STATUS_PENDING
                )
                if tenant_invite.is_expired():
                    return None, None, Response({
                        "success": False,
                        "error": {"message": "Invitation expired. Please contact admin."}
                    }, status=status.HTTP_400_BAD_REQUEST)
                return tenant_invite, True, None
            except TenantInvite.DoesNotExist:
                return None, None, Response({
                    "success": False,
                    "error": {
                        "message": "Invitation required",
                        "details": "This platform is invite-only. Please contact admin for an invitation."
                    }
                }, status=status.HTTP_403_FORBIDDEN)

    def _process_membership(self, user, validated_invite, is_tenant_signup, invite_token):
        if validated_invite and not is_tenant_signup:
            if isinstance(validated_invite, dict):
                tenant = Tenant.objects.get(id=validated_invite['tenant_id'])
                TenantMember.objects.create(tenant=tenant, user=user, role=validated_invite['role'])
                RedisInviteManager.delete_invite(invite_token)
            elif validated_invite.is_valid():
                TenantMember.objects.create(
                    tenant=validated_invite.tenant, user=user, role=validated_invite.role
                )
                validated_invite.mark_accepted()
        elif is_tenant_signup:
            # Prefer company name from approved access request, fallback to user info
            tenant_name = None
            access_request = AccessRequest.objects.filter(email=user.email, status=AccessRequest.STATUS_APPROVED).order_by('-created_at').first()
            if access_request and access_request.company_name:
                tenant_name = access_request.company_name
            if not tenant_name:
                tenant_name = f"{user.first_name}'s Tenant" if user.first_name else f"{user.email.split('@')[0]}'s Tenant"
            tenant = Tenant.objects.create(name=tenant_name, created_by=user)
            TenantMember.objects.create(tenant=tenant, user=user, role=TenantMember.ROLE_OWNER)
            if validated_invite:
                validated_invite.mark_registered(user)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Login user",
        request=LoginSerializer,
        responses={200: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT},
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        # Manually verify user credentials so we can distinguish between
        # "invalid credentials" and "account blocked / disabled".
        user = User.objects.filter(email=email).first()
        
        if not user or not user.check_password(password):
            return Response({
                "success": False,
                "error": {
                    "message": "Invalid credentials",
                    "details": "Email or password is incorrect"
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({
                "success": False,
                "error": {
                    "message": "Your account is blocked",
                    "details": "Your account has been blocked. Please contact the administrator."
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if user's tenant is blocked
        if hasattr(user, 'tenant_membership') and user.tenant_membership:
            tenant = user.tenant_membership.tenant
            if not tenant.is_active:
                return Response({
                    "success": False,
                    "error": {
                        "message": "Your account is blocked",
                        "details": "Your tenant account has been blocked. Please contact the administrator."
                    }
                }, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        
        return Response({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.get_role(),
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Logout user",
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        tags=["Authentication"]
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        
        if not refresh_token:
            return Response({
                "success": False,
                "error": {
                    "message": "Refresh token required",
                    "details": "Please provide refresh token in request body"
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                "success": True,
                "message": "Logged out successfully"
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                "success": False,
                "error": {
                    "message": "Logout failed",
                    "details": "Invalid or expired refresh token"
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class SendOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Send OTP",
        request=SendOTPSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": {
                    "message": "Invalid data",
                    "details": serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        success, message = send_otp_email(email)
        
        if success:
            return Response({
                "success": True,
                "message": message
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": False,
                "error": {"message": message}
            }, status=status.HTTP_429_TOO_MANY_REQUESTS if "wait" in message else status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify OTP",
        request=VerifyOTPSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": {
                    "message": "Invalid data",
                    "details": serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        
        token, message = verify_otp_code(email, otp)
        
        if token:
            return Response({
                "success": True,
                "message": message,
                "verification_token": token
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": False,
                "error": {"message": message}
            }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Reset Password",
        request=ResetPasswordSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": {
                    "message": "Invalid data",
                    "details": serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = get_object_or_404(User, email=email)
        user.set_password(password)
        user.save()
        
        return Response({
            "success": True,
            "message": "Password reset successfully. Please login with new password."
        }, status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get or Update User Profile",
        responses={200: UserSerializer},
        tags=["Authentication"]
    )
    def get(self, request):
        # Check if user's tenant is blocked (only for non-admin users)
        # Skip tenant blocking check for admin users
        if not request.user.is_staff and not request.user.is_superuser:
            if hasattr(request.user, 'tenant_membership') and request.user.tenant_membership:
                tenant = request.user.tenant_membership.tenant
                if not tenant.is_active:
                    return Response({
                        "success": False,
                        "error": {
                            "message": "Your account is blocked",
                            "details": "Your tenant account has been blocked. Please contact the administrator."
                        }
                    }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = UserSerializer(request.user)
        return Response({
            "success": True,
            "user": serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request)

    def _update(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Profile updated successfully",
                "user": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "success": False,
            "error": {
                "message": "Validation failed",
                "details": serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)



class RequestAccessView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Request Access (Waitlist)",
        request=AccessRequestSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["Authentication"]
    )
    def post(self, request):
        from django.core.cache import cache
        
        ip = request.META.get('REMOTE_ADDR')
        cache_key = f"request_access_rate_limit_{ip}"
        requests_count = cache.get(cache_key, 0)
        
        if requests_count >= 1:
            return Response({
                "success": False,
                "error": {
                    "message": "Rate limit exceeded",
                    "details": "You have made too many requests. Please try again later."
                }
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        cache.set(cache_key, requests_count + 1, timeout=3600)
        
        serializer = AccessRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Request received. We will contact you shortly."
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "error": {
                "message": "Invalid data",
                "details": serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)


register = RegisterView.as_view()
login = LoginView.as_view()
logout = LogoutView.as_view()
send_otp = SendOTPView.as_view()
verify_otp = VerifyOTPView.as_view()
reset_password = ResetPasswordView.as_view()
profile = ProfileView.as_view()
request_access = RequestAccessView.as_view()
