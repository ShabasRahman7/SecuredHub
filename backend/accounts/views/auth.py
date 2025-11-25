from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers import RegisterSerializer, LoginSerializer, UserSerializer, SendOTPSerializer, VerifyOTPSerializer, ResetPasswordSerializer
from ..serializers.access_request import AccessRequestSerializer
from ..models import TenantInvite, TenantMember
from django.shortcuts import get_object_or_404
import logging
from ..utils.otp import send_otp_email, verify_otp_code

logger = logging.getLogger(__name__)

@extend_schema(
    summary="Register a new user (Invite-Only)",
    description="Register with valid invitation token. Tenants need admin invite, developers need tenant invite.",
    request=RegisterSerializer,
    responses={201: RegisterSerializer},
    tags=["Authentication"]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register new user account (invite-only)."""
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        invite_token = request.data.get('invite_token')
        email = serializer.validated_data['email']
        
        from django.contrib.auth import get_user_model
        from ..models import TenantInvite, MemberInvite, TenantMember, Tenant
        from ..utils.email import verify_tenant_invite_token
        
        User = get_user_model()
        
        # Determine context based on invite
        is_tenant_signup = False
        validated_invite = None
        
        # Check for developer invite (Redis-based MemberInvite)
        if invite_token:
            from ..utils.redis_invites import RedisInviteManager
            
            # Try Redis first (member invites)
            invite_data = RedisInviteManager.get_invite_by_token(invite_token)
            
            if invite_data:
                # Redis invite found
                if RedisInviteManager.is_expired(invite_data):
                    return Response({
                        "success": False,
                        "error": {"message": "Invitation expired. Please request a new one."}
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if invite_data['email'] != email:
                    return Response({
                        "success": False,
                        "error": {"message": "Email doesn't match invitation"}
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Store invite data for later use
                validated_invite = invite_data
                is_tenant_signup = (invite_data.get('type') == 'tenant')
            else:
                # Try database (legacy tenant invites)
                tenant_invite, error = verify_tenant_invite_token(invite_token)
                if error or not tenant_invite:
                    return Response({
                        "success": False,
                        "error": {"message": "Invalid or expired invitation"}
                    }, status=status.HTTP_400_BAD_REQUEST)
                if tenant_invite.email != email:
                    return Response({
                        "success": False,
                        "error": {"message": "Email doesn't match invitation"}
                    }, status=status.HTTP_400_BAD_REQUEST)
                is_tenant_signup = True
                validated_invite = tenant_invite
        else:
            # No invite token - check if there's a pending TenantInvite for this email
            try:
                tenant_invite = TenantInvite.objects.get(email=email, status=TenantInvite.STATUS_PENDING)
                if tenant_invite.is_expired():
                    return Response({
                        "success": False,
                        "error": {"message": "Invitation expired. Please contact admin."}
                    }, status=status.HTTP_400_BAD_REQUEST)
                is_tenant_signup = True
                validated_invite = tenant_invite
            except TenantInvite.DoesNotExist:
                return Response({
                    "success": False,
                    "error": {
                        "message": "Invitation required",
                        "details": "This platform is invite-only. Please contact admin for an invitation."
                    }
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Create user
        user = serializer.save()
        
        # Handle invite token if present (Developer joining existing tenant)
        if validated_invite and not is_tenant_signup:
            from ..utils.redis_invites import RedisInviteManager
            
            # Check if it's a Redis invite (dict) or database invite (object)
            if isinstance(validated_invite, dict):
                # Redis invite
                tenant = Tenant.objects.get(id=validated_invite['tenant_id'])
                TenantMember.objects.create(
                    tenant=tenant,
                    user=user,
                    role=validated_invite['role']
                )
                # Delete invite from Redis (mark as accepted)
                RedisInviteManager.delete_invite(invite_token)
                logger.info(f"User {user.email} joined tenant {tenant.name} via Redis invite")
            else:
                # Database invite (legacy)
                if validated_invite.is_valid():
                    TenantMember.objects.create(
                        tenant=validated_invite.tenant,
                        user=user,
                        role=validated_invite.role
                    )
                    validated_invite.mark_accepted()
                    logger.info(f"User {user.email} joined tenant {validated_invite.tenant.name} via database invite")
        
        # Auto-create organization for Tenants (New Tenant)
        elif is_tenant_signup:
            tenant_name = f"{user.first_name}'s Tenant" if user.first_name else f"{user.email.split('@')[0]}'s Tenant"
            tenant = Tenant.objects.create(
                name=tenant_name,
                created_by=user
            )
            # Add owner membership
            TenantMember.objects.create(
                tenant=tenant,
                user=user,
                role=TenantMember.ROLE_OWNER
            )
            logger.info(f"Auto-created tenant '{tenant.name}' for new tenant {user.email}")
            
            # Mark TenantInvite as registered
            if validated_invite:
                validated_invite.mark_registered(user)
                logger.info(f"Marked TenantInvite as registered for {user.email}")
        
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"New user registered: {user.email}")
        
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
    
    logger.warning(f"Registration failed: {serializer.errors}")
    return Response({
        "success": False,
        "error": {
            "message": "Registration failed",
            "details": serializer.errors
        }
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Login user",
    description="Authenticate user and return JWT access and refresh tokens.",
    request=LoginSerializer,
    responses={
        200: OpenApiTypes.OBJECT,
        401: OpenApiTypes.OBJECT,
    },
    tags=["Authentication"]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Authenticate user and return JWT tokens.
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    user = authenticate(request, email=email, password=password)
    
    if not user:
        logger.warning(f"Failed login attempt for email: {email}")
        return Response({
            "success": False,
            "error": {
                "message": "Invalid credentials",
                "details": "Email or password is incorrect"
            }
        }, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        logger.warning(f"Inactive user login attempt: {email}")
        return Response({
            "success": False,
            "error": {
                "message": "Account disabled",
                "details": "This account has been deactivated"
            }
        }, status=status.HTTP_403_FORBIDDEN)

    refresh = RefreshToken.for_user(user)
    
    logger.info(f"User logged in: {user.email}")
    
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


@extend_schema(
    summary="Logout user",
    description="Logout user by blacklisting their refresh token.",
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT},
    tags=["Authentication"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by blacklisting their refresh token.
    """
    try:
        refresh_token = request.data.get("refresh")
        
        if not refresh_token:
            return Response({
                "success": False,
                "error": {
                    "message": "Refresh token required",
                    "details": "Please provide refresh token in request body"
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        logger.info(f"User logged out: {request.user.email}")
        
        return Response({
            "success": True,
            "message": "Logged out successfully"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({
            "success": False,
            "error": {
                "message": "Logout failed",
                "details": "Invalid or expired refresh token"
            }
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Send OTP",
    description="Send OTP to the provided email address for verification.",
    request=SendOTPSerializer,
    responses={200: OpenApiTypes.OBJECT},
    tags=["Authentication"]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    """
    Send OTP to the provided email address.
    """
    serializer = SendOTPSerializer(data=request.data)
    if serializer.is_valid():
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
                "error": {
                    "message": message
                }
            }, status=status.HTTP_429_TOO_MANY_REQUESTS if "wait" in message else status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    return Response({
        "success": False,
        "error": {
            "message": "Invalid data",
            "details": serializer.errors
        }
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Verify OTP",
    description="Verify the OTP code sent to the email.",
    request=VerifyOTPSerializer,
    responses={200: OpenApiTypes.OBJECT},
    tags=["Authentication"]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    Verify the OTP code.
    """
    serializer = VerifyOTPSerializer(data=request.data)
    if serializer.is_valid():
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
                "error": {
                    "message": message
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
    return Response({
        "success": False,
        "error": {
            "message": "Invalid data",
            "details": serializer.errors
        }
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Reset Password",
    description="Reset user password using verified OTP token.",
    request=ResetPasswordSerializer,
    responses={200: OpenApiTypes.OBJECT},
    tags=["Authentication"]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Reset user password.
    """
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = get_object_or_404(User, email=email)
        
        user.set_password(password)
        user.save()
        
        logger.info(f"Password reset for user: {email}")
        
        return Response({
            "success": True,
            "message": "Password reset successfully. Please login with new password."
        }, status=status.HTTP_200_OK)
            
    return Response({
        "success": False,
        "error": {
            "message": "Invalid data",
            "details": serializer.errors
        }
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Get or Update User Profile",
    description="Get or update current user profile information.",
    responses={200: UserSerializer},
    tags=["Authentication"]
)
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Get or update current user profile information.
    
    GET /api/v1/auth/profile/
    PUT/PATCH /api/v1/auth/profile/
    """
    user = request.user
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response({
            "success": True,
            "user": serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = UserSerializer(user, data=request.data, partial=True)
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


@extend_schema(
    summary="Admin List Users",
    description="List all developers (admin only).",
    responses={200: UserSerializer(many=True)},
    tags=["Admin"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_list_users(request):
    """
    List all developers (admin only).
    
    GET /api/v1/auth/admin/users/
    """
    if not request.user.is_superuser:
        return Response({
            "success": False,
            "error": {
                "message": "Permission denied",
                "details": "Only administrators can view all users"
            }
        }, status=status.HTTP_403_FORBIDDEN)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    # Filter for developers only
    users = User.objects.filter(tenant_memberships__role=TenantMember.ROLE_DEVELOPER).distinct().order_by('-date_joined')
    
    # Add tenant information to each user
    users_data = []
    for user in users:
        user_dict = UserSerializer(user).data
        
        # Get all tenants this user belongs to
        memberships = TenantMember.objects.filter(user=user).select_related('tenant')
        tenants = [{
            'id': m.tenant.id,
            'name': m.tenant.name,
            'role': m.role
        } for m in memberships]
        
        user_dict['tenants'] = tenants
        users_data.append(user_dict)
    
    return Response({
        "success": True,
        "count": users.count(),
        "users": users_data
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Request Access (Waitlist)",
    description="Submit a request for access to the platform (Rate limited).",
    request=AccessRequestSerializer,
    responses={200: OpenApiTypes.OBJECT},
    tags=["Authentication"]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def request_access(request):
    """
    Submit a request for access (Waitlist).
    Rate limited to 5 requests per hour per IP using Redis.
    """
    from django.core.cache import cache
    from ..serializers.access_request import AccessRequestSerializer
    
    # Rate Limiting Logic
    ip = request.META.get('REMOTE_ADDR')
    cache_key = f"request_access_rate_limit_{ip}"
    requests_count = cache.get(cache_key, 0)
    
    if requests_count >= 5:
        return Response({
            "success": False,
            "error": {
                "message": "Rate limit exceeded",
                "details": "You have made too many requests. Please try again later."
            }
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Increment rate limit counter (expire in 1 hour)
    cache.set(cache_key, requests_count + 1, timeout=3600)
    
    serializer = AccessRequestSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        logger.info(f"New access request from {serializer.validated_data['email']}")
        
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
