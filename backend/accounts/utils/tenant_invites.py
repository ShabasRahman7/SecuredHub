"""
Utilities for sending organization invites.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def send_invite_email(invite):
    """
    Send invitation email to a user.
    
    Args:
        invite: MemberInvite instance
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        subject = f"You're invited to join {invite.tenant.name} on SecuredHub"
        
        # Build invite URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        invite_url = f"{frontend_url}/accept-invite?token={invite.token}"
        
        message = f"""
Hello,

{invite.invited_by.first_name or invite.invited_by.email} has invited you to join {invite.tenant.name} on SecuredHub.

Click the link below to accept the invitation:
{invite_url}

This invitation will expire on {invite.expires_at.strftime('%B %d, %Y at %H:%M UTC')}.

If you don't have an account yet, you can create one using this email address.

Best regards,
SecuredHub Team
"""
        
        from_email = settings.EMAIL_HOST_USER or 'noreply@securedhub.com'
        
        send_mail(
            subject,
            message,
            from_email,
            [invite.email],
            fail_silently=False
        )
        
        # Update last_sent_at
        invite.last_sent_at = timezone.now()
        invite.save(update_fields=['last_sent_at'])
        
        logger.info(f"Invite email sent to {invite.email} for tenant {invite.tenant.name}")
        return True, "Invitation email sent successfully"
        
    except Exception as e:
        logger.error(f"Failed to send invite email to {invite.email}: {str(e)}")
        return False, f"Failed to send email: {str(e)}"


def can_resend_invite(invite):
    """
    Check if an invite can be resent based on exponential backoff.
    
    Args:
        invite: MemberInvite instance
        
    Returns:
        tuple: (can_resend: bool, wait_minutes: int, message: str)
    """
    if not invite.last_sent_at:
        return True, 0, "Can send now"
    
    # Calculate cooldown (5 * 2^resend_count minutes)
    base_cooldown = 5
    cooldown_minutes = base_cooldown * (2 ** invite.resend_count)
    
    # Cap at 60 minutes
    cooldown_minutes = min(cooldown_minutes, 60)
    
    time_since_last = timezone.now() - invite.last_sent_at
    required_wait = timedelta(minutes=cooldown_minutes)
    
    if time_since_last >= required_wait:
        return True, 0, "Can resend now"
    else:
        minutes_remaining = int((required_wait - time_since_last).total_seconds() / 60) + 1
        return False, minutes_remaining, f"Please wait {minutes_remaining} more minutes before resending"


def resend_invite_email(invite):
    """
    Resend an invitation email with exponential backoff.
    
    Args:
        invite: MemberInvite instance
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Check if can resend
    can_resend, wait_minutes, check_message = can_resend_invite(invite)
    
    if not can_resend:
        return False, check_message
    
    # Send the email
    success, message = send_invite_email(invite)
    
    if success:
        invite.resend_count += 1
        invite.save(update_fields=['resend_count'])
        
    return success, message



def send_member_invite_email(email, tenant_name, invited_by_name, token):
    """
    Send invitation email to a user (Redis-based).
    
    Args:
        email: Email address to send to
        tenant_name: Name of the tenant
        invited_by_name: Name of person who sent invite
        token: Invite token
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        subject = f"You're invited to join {tenant_name} on SecuredHub"
        
        # Build invite URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        invite_url = f"{frontend_url}/accept-invite/{token}"
        
        message = f"""
Hello,

{invited_by_name} has invited you to join {tenant_name} on SecuredHub as a Developer.

Click the link below to accept the invitation:
{invite_url}

This invitation will expire in 24 hours.

If you don't have an account yet, you'll be guided through the registration process.

Best regards,
SecuredHub Team
"""
        
        from_email = settings.EMAIL_HOST_USER or 'noreply@securedhub.com'
        
        send_mail(
            subject,
            message,
            from_email,
            [email],
            fail_silently=False
        )
        
        logger.info(f"Invite email sent to {email} for tenant {tenant_name}")
        return True, "Invitation email sent successfully"
        
    except Exception as e:
        logger.error(f"Failed to send invite email to {email}: {str(e)}")
        return False, f"Failed to send email: {str(e)}"
