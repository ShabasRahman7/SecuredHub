import random
import string
from django.core.mail import send_mail
from django.core.cache import cache
from django.conf import settings
import time

OTP_EXPIRY = 300  # 5 minutes
VERIFIED_TOKEN_EXPIRY = 900  # 15 minutes

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def get_rate_limit_key(email):
    return f"otp_limit:{email}"

def get_otp_key(email):
    return f"otp:{email}"

def get_verified_key(email):
    return f"otp_verified:{email}"

def check_rate_limit(email):
    # exponential backoff: 1m, 5m, 15m
    key = get_rate_limit_key(email)
    data = cache.get(key)
    
    if not data:
        return True, 0
    
    last_sent = data['last_sent']
    count = data['count']
    
    now = time.time()
    elapsed = now - last_sent
    
    if count == 1:
        wait = 60
    elif count == 2:
        wait = 300
    else:
        wait = 900
        
    if elapsed < wait:
        return False, int(wait - elapsed)
        
    return True, 0

def increment_rate_limit(email):
    key = get_rate_limit_key(email)
    data = cache.get(key)
    
    now = time.time()
    
    if not data:
        new_data = {'count': 1, 'last_sent': now}
    else:
        # reset if > 1 hour
        if now - data['last_sent'] > 3600:
            new_data = {'count': 1, 'last_sent': now}
        else:
            new_data = {'count': data['count'] + 1, 'last_sent': now}
            
    cache.set(key, new_data, timeout=86400)

def send_otp_email(email, context='register'):
    allowed, wait_time = check_rate_limit(email)
    if not allowed:
        return False, f"Please wait {wait_time} seconds before resending OTP."
        
    otp = generate_otp()
    
    if context == 'tenant_invite':
        subject = "SecuredHub - Tenant Registration Invitation"
        message = f"""Hello,

You have been invited by an administrator to register as a Tenant on SecuredHub.

Your verification code is: {otp}

This code expires in 5 minutes.

After verifying this code, you'll be able to complete your registration and create your organization on our platform.

If you did not expect this invitation, please ignore this email.

Best regards,
SecuredHub Team"""
    elif context == 'password_reset':
        subject = "SecuredHub - Password Reset Code"
        message = f"""Your password reset verification code is: {otp}

This code expires in 5 minutes.

If you did not request a password reset, please ignore this email.

Best regards,
SecuredHub Team"""
    else:  # Default: registration
        subject = "SecuredHub - Verification Code"
        message = f"""Your verification code is: {otp}

This code expires in 5 minutes.

Complete your registration to get started with SecuredHub.

Best regards,
SecuredHub Team"""
    
    from_email = settings.EMAIL_HOST_USER
    
    try:
        send_mail(subject, message, from_email, [email], fail_silently=False)
        
        cache.set(get_otp_key(email), otp, timeout=OTP_EXPIRY)
        
        increment_rate_limit(email)
        
        return True, "OTP sent successfully."
        
    except Exception as e:
        return False, "Failed to send email. Please try again later."

def get_otp_attempts_key(email):
    return f"otp_attempts:{email}"

def check_otp_attempts(email):
    # max 3 attempts, 15-minute lockout
    key = get_otp_attempts_key(email)
    data = cache.get(key)
    
    if not data:
        return True, None, 3
    
    attempts = data.get('attempts', 0)
    locked_until = data.get('locked_until')
    
    now = time.time()
    
    if locked_until and now < locked_until:
        wait_time = int(locked_until - now)
        return False, locked_until, 0
    
    if locked_until and now >= locked_until:
        cache.delete(key)
        return True, None, 3
    
    remaining = max(0, 3 - attempts)
    return remaining > 0, None, remaining

def increment_otp_attempts(email):
    key = get_otp_attempts_key(email)
    data = cache.get(key) or {'attempts': 0}
    
    data['attempts'] += 1
    
    if data['attempts'] >= 3:
        lockout_duration = 900
        data['locked_until'] = time.time() + lockout_duration
    
    cache.set(key, data, timeout=1800)
    return data['attempts']

def reset_otp_attempts(email):
    cache.delete(get_otp_attempts_key(email))

def verify_otp_code(email, code):
    allowed, locked_until, remaining = check_otp_attempts(email)
    
    if not allowed:
        wait_minutes = int((locked_until - time.time()) / 60) + 1
        return None, f"Too many failed attempts. Please try again in {wait_minutes} minutes."
    
    stored_otp = cache.get(get_otp_key(email))
    
    if not stored_otp:
        return None, "OTP expired or not found."
        
    if stored_otp != code:
        attempts = increment_otp_attempts(email)
        remaining_attempts = max(0, 3 - attempts)
        
        if remaining_attempts == 0:
            return None, "Invalid OTP. Too many failed attempts. Account locked for 15 minutes."
        else:
            return None, f"Invalid OTP. {remaining_attempts} attempt(s) remaining."
        
    cache.delete(get_otp_key(email))
    reset_otp_attempts(email)
    
    verification_token = generate_otp(32)
    cache.set(get_verified_key(email), verification_token, timeout=VERIFIED_TOKEN_EXPIRY)
    
    return verification_token, "OTP verified successfully."

def check_verification_token(email, token):
    try:
        stored_token = cache.get(get_verified_key(email))
    except Exception:
        # if cache/Redis is unavailable, treat as invalid to avoid 500s
        return False
    return stored_token and stored_token == token
