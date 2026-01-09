# unit tests for accounts OTP utilities
import pytest
import time
from unittest.mock import patch, MagicMock
from accounts.utils.otp import (
    generate_otp,
    check_rate_limit,
    increment_rate_limit,
    send_otp_email,
    check_otp_attempts,
    increment_otp_attempts,
    reset_otp_attempts,
    verify_otp_code,
    check_verification_token,
    get_otp_key,
    get_verified_key,
    get_rate_limit_key,
    get_otp_attempts_key
)


@pytest.mark.unit
class TestOTPGeneration:
    # testing OTP generation logic
    
    def test_generate_otp_default_length(self):
        # should generate 6-digit OTP by default
        otp = generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()
    
    def test_generate_otp_custom_length(self):
        # should generate OTP with custom length
        otp = generate_otp(length=8)
        assert len(otp) == 8
        assert otp.isdigit()
    
    def test_generate_otp_uniqueness(self):
        # should generate different OTPs on successive calls
        otp1 = generate_otp()
        otp2 = generate_otp()
        # highly unlikely to be equal
        assert otp1 != otp2 or len({generate_otp() for _ in range(10)}) > 1


@pytest.mark.unit
@pytest.mark.django_db
class TestRateLimiting:
    # testing rate limiting with exponential backoff
    
    def test_first_request_allowed(self, mock_redis_cache):
        # should allow first OTP request
        email = "test@example.com"
        allowed, wait_time = check_rate_limit(email)
        
        assert allowed is True
        assert wait_time == 0
    
    def test_second_request_within_one_minute_blocked(self, mock_redis_cache):
        # should block second request within 1 minute
        email = "test@example.com"
        
        # first request
        increment_rate_limit(email)
        
        # immediate second request
        allowed, wait_time = check_rate_limit(email)
        
        assert allowed is False
        assert wait_time > 0
        assert wait_time <= 60
    
    def test_third_request_within_five_minutes_blocked(self, mock_redis_cache):
        # should block third request within 5 minutes (escalated)
        email = "test@example.com"
        
        # simulating 2 previous requests
        key = get_rate_limit_key(email)
        mock_redis_cache.get.return_value = {
            'count': 2,
            'last_sent': time.time()
        }
        
        allowed, wait_time = check_rate_limit(email)
        
        assert allowed is False
        assert wait_time <= 300
    
    def test_request_after_wait_period_allowed(self, mock_redis_cache):
        # should allow request after wait period expires
        email = "test@example.com"
        
        # simulating old request (>1 hour ago)
        key = get_rate_limit_key(email)
        mock_redis_cache.get.return_value = {
            'count': 1,
            'last_sent': time.time() - 3700
        }
        
        allowed, wait_time = check_rate_limit(email)
        
        assert allowed is True
        assert wait_time == 0


@pytest.mark.unit
@pytest.mark.django_db
class TestOTPVerification:
    # testing OTP verification with brute-force protection
    
    def test_verify_valid_otp_success(self, mock_redis_cache):
        # should verify valid OTP and return verification token
        email = "test@example.com"
        otp = "123456"
        
        # mocking stored OTP
        def mock_cache_get(key):
            if key == get_otp_key(email):
                return otp
            return None
        
        mock_redis_cache.get.side_effect = mock_cache_get
        
        token, message = verify_otp_code(email, otp)
        
        assert token is not None
        assert len(token) == 32
        assert message == "OTP verified successfully."
    
    def test_verify_invalid_otp_fails(self, mock_redis_cache):
        # should reject invalid OTP and increment attempts
        email = "test@example.com"
        
        def mock_cache_get(key):
            if key == get_otp_key(email):
                return "123456"
            return None
        
        mock_redis_cache.get.side_effect = mock_cache_get
        
        token, message = verify_otp_code(email, "wrong_otp")
        
        assert token is None
        assert "Invalid OTP" in message
        assert "2 attempt(s) remaining" in message
    
    def test_verify_expired_otp_fails(self, mock_redis_cache):
        # should reject when OTP not found in cache
        email = "test@example.com"
        
        mock_redis_cache.get.return_value = None
        
        token, message = verify_otp_code(email, "123456")
        
        assert token is None
        assert "expired or not found" in message
    
    def test_brute_force_lockout_after_three_attempts(self, mock_redis_cache):
        # should lock account after 3 failed validation attempts
        email = "test@example.com"
        
        # simulating 3 failed attempts
        attempt_data = {'attempts': 3, 'locked_until': time.time() + 900}
        
        def mock_cache_get(key):
            if key == get_otp_attempts_key(email):
                return attempt_data
            if key == get_otp_key(email):
                return "123456"
            return None
        
        mock_redis_cache.get.side_effect = mock_cache_get
        
        token, message = verify_otp_code(email, "wrong_code")
        
        assert token is None
        assert "locked" in message.lower() or "many" in message.lower()
    
    def test_reset_attempts_after_success(self, mock_redis_cache):
        # should reset attempts counter after successful verification
        email = "test@example.com"
        
        reset_otp_attempts(email)
        
        # verifying delete was called for attempts key
        mock_redis_cache.delete.assert_called()


@pytest.mark.unit
@pytest.mark.django_db
class TestVerificationToken:
    # testing verification token generation and validation
    
    def test_check_verification_token_valid(self, mock_redis_cache):
        # should validate correct verification token
        email = "test@example.com"
        token = "valid_token_12345"
        
        mock_redis_cache.get.return_value = token
        
        result = check_verification_token(email, token)
        
        assert result is True
    
    def test_check_verification_token_invalid(self, mock_redis_cache):
        # should reject invalid verification token
        email = "test@example.com"
        
        mock_redis_cache.get.return_value = "correct_token"
        
        result = check_verification_token(email, "wrong_token")
        
        assert result is False
    
    def test_check_verification_token_expired(self, mock_redis_cache):
        # should reject when token not in cache
        email = "test@example.com"
        
        mock_redis_cache.get.return_value = None
        
        result = check_verification_token(email, "any_token")
        
        assert result is False
    
    def test_check_verification_token_handles_cache_failure(self, mock_redis_cache):
        # should handle Redis/cache failure gracefully
        email = "test@example.com"
        
        mock_redis_cache.get.side_effect = Exception("Redis connection failed")
        
        result = check_verification_token(email, "token")
        
        # should treat as invalid to avoid 500 errors
        assert result is False


@pytest.mark.unit
@pytest.mark.django_db
class TestOTPEmail:
    # testing OTP email sending with rate limiting
    
    def test_send_otp_email_success(self, mock_redis_cache, mock_send_mail):
        # should send OTP email successfully
        email = "test@example.com"
        
        mock_redis_cache.get.return_value = None  # no rate limit
        
        success, message = send_otp_email(email)
        
        assert success is True
        assert "successfully" in message.lower()
        mock_send_mail.assert_called_once()
    
    def test_send_otp_email_rate_limited(self, mock_redis_cache, mock_send_mail):
        # should reject when rate limited
        email = "test@example.com"
        
        # simulating rate limit
        mock_redis_cache.get.return_value = {
            'count': 1,
            'last_sent': time.time()
        }
        
        success, message = send_otp_email(email)
        
        assert success is False
        assert "wait" in message.lower()
        mock_send_mail.assert_not_called()
    
    def test_send_otp_email_with_context_tenant_invite(self, mock_redis_cache, mock_send_mail):
        # should customize email for tenant invite context
        email = "invite@example.com"
        
        mock_redis_cache.get.return_value = None
        
        success, message = send_otp_email(email, context='tenant_invite')
        
        assert success is True
        # checking that the correct subject was used
        call_args = mock_send_mail.call_args
        assert "Tenant Registration" in call_args[0][0]
    
    def test_send_otp_email_handles_smtp_failure(self, mock_redis_cache, mock_send_mail):
        # should handle SMTP failure gracefully
        email = "test@example.com"
        
        mock_redis_cache.get.return_value = None
        mock_send_mail.side_effect = Exception("SMTP error")
        
        success, message = send_otp_email(email)
        
        assert success is False
        assert "Failed to send" in message or "try again" in message
