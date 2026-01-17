from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

def send_tenant_invite_email(tenant_invite):
    email = tenant_invite.email
    token = tenant_invite.token
    
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
        
        return True, "Invitation email sent successfully."
        
    except Exception as e:
        return False, "Failed to send invitation email. Please try again later."

def send_access_request_rejection_email(email):
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
        
        return True, "Rejection email sent successfully."
        
    except Exception as e:
        return False, "Failed to send rejection email."

def verify_tenant_invite_token(token):
    from ..models import TenantInvite
    from .redis_tokens import InviteTokenManager
    
    # Redis is optional here - database is the source of truth
    try:
        email = InviteTokenManager.verify_token(str(token))
    except Exception:
        email = None
    
    try:
        invite = TenantInvite.objects.get(token=token)
    except TenantInvite.DoesNotExist:
        return None, "Invalid invitation token."
    
    if email and invite.email != email:
        return None, "Invalid invitation token."
    
    if invite.status == TenantInvite.STATUS_REGISTERED:
        return None, "This invitation has already been used."
    
    if invite.expires_at and invite.expires_at < timezone.now():
        invite.status = TenantInvite.STATUS_EXPIRED
        invite.save(update_fields=['status'])
        return None, "This invitation has expired."
    
    return invite, None

