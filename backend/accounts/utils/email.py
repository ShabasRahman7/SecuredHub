"""
Utility functions for tenant invitation emails.
"""
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger('api')


def send_tenant_invite_email(tenant_invite):
    """
    Send tenant invitation email with secure signup link.
    
    Args:
        tenant_invite: TenantInvite model instance
        
    Returns:
        (success: bool, message: str)
    """
    email = tenant_invite.email
    token = tenant_invite.token
    
    # Build the registration URL with invite token
    frontend_url = settings.FRONTEND_URL.rstrip('/')
    signup_url = f"{frontend_url}/register?invite_token={token}&type=tenant"
    
    subject = "SecuredHub - Tenant Registration Invitation"
    
    message = f"""Hello,
    
You have been invited by an administrator to join SecuredHub as a Tenant.
    
Click the link below to complete your registration:
    
{signup_url}
    
This invitation link will expire in 24 hours.
    
After clicking the link, you'll be able to:
• Create your tenant on our platform
• Invite developers to join your team
• Manage your repositories securely
    
If you did not expect this invitation, please ignore this email.
    
Need help? Contact our support team.
    
Best regards,
SecuredHub Team
"""
    
    from_email = settings.EMAIL_HOST_USER
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False
        )
        
        logger.info(f"Tenant invitation email sent to {email} (token: {token})")
        return True, "Invitation email sent successfully."
        
    except Exception as e:
        logger.error(f"Failed to send tenant invitation to {email}: {str(e)}")
        return False, "Failed to send invitation email. Please try again later."


def send_access_request_rejection_email(email):
    """
    Send access request rejection email.
    
    Args:
        email: Email address of the rejected user
        
    Returns:
        (success: bool, message: str)
    """
    subject = "SecuredHub - Access Request Update"
    
    message = f"""Hello,
    
Thank you for your interest in SecuredHub.
    
We have reviewed your request for access to our platform. unfortunately, we are unable to approve your request at this time.
    
If you believe this decision was made in error or if you have additional information to provide, please contact our support team.
    
Best regards,
SecuredHub Team
"""
    
    from_email = settings.EMAIL_HOST_USER
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False
        )
        
        logger.info(f"Access request rejection email sent to {email}")
        return True, "Rejection email sent successfully."
        
    except Exception as e:
        logger.error(f"Failed to send rejection email to {email}: {str(e)}")
        return False, "Failed to send rejection email."


def verify_tenant_invite_token(token):
    """
    Verify a tenant invitation token.
    
    Args:
        token: UUID invitation token
        
    Returns:
        (tenant_invite: TenantInvite|None, error_message: str|None)
    """
    from ..models import TenantInvite
    from .redis_tokens import InviteTokenManager
    
    # First check Redis for fast expiration validation
    email = InviteTokenManager.verify_token(str(token))
    if not email:
        # Token not in Redis = expired or invalid
        return None, "This invitation has expired or is invalid."
    
    # Token is in Redis, now validate database record
    try:
        invite = TenantInvite.objects.get(token=token)
        
        # Email mismatch check
        if invite.email != email:
            logger.warning(f"Email mismatch for token {token}: DB={invite.email}, Redis={email}")
            return None, "Invalid invitation token."
        
        if invite.status == TenantInvite.STATUS_REGISTERED:
            return None, "This invitation has already been used."
        
        if invite.status == TenantInvite.STATUS_EXPIRED:
            return None, "This invitation has expired."
        
        # Valid invite
        return invite, None
        
    except TenantInvite.DoesNotExist:
        return None, "Invalid invitation token."

