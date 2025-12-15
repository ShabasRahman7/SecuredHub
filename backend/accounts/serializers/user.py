from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from ..utils.otp import check_verification_token
from ..models import AccessRequest

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Confirm Password'
    )
    verification_token = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Token received after verifying OTP"
    )
    invite_token = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Optional invite token for joining an organization"
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'password2', 'first_name', 'last_name', 'verification_token', 'invite_token']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
            
        email = attrs.get('email')
        token = attrs.get('verification_token')
        
        if not check_verification_token(email, token):
            raise serializers.ValidationError({
                "verification_token": "Invalid or expired verification token. Please verify email first."
            })
            
        return attrs

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        validated_data.pop('password2')
        validated_data.pop('verification_token')
        invite_token = validated_data.pop('invite_token', None)
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined', 'is_superuser', 'is_staff']
        read_only_fields = ['id', 'email', 'role', 'is_active', 'date_joined', 'is_superuser', 'is_staff']
    
    def get_role(self, obj):
        return obj.get_role()


class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    type = serializers.ChoiceField(choices=['register', 'reset_password'], default='register', required=False)

    def validate(self, attrs):
        email = attrs.get('email')
        otp_type = attrs.get('type', 'register')
        
        user_exists = User.objects.filter(email=email).exists()
        
        if otp_type == 'register' and user_exists:
            raise serializers.ValidationError({"email": "User with this email already exists."})
            
        if otp_type == 'reset_password' and not user_exists:
            raise serializers.ValidationError({"email": "No user found with this email address."})
            
        return attrs


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6, min_length=6)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    verification_token = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
            
        email = attrs.get('email')
        token = attrs.get('verification_token')
        
        if not check_verification_token(email, token):
            raise serializers.ValidationError({
                "verification_token": "Invalid or expired verification token. Please verify email first."
            })
            
        return attrs


class AccessRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRequest
        fields = ['id', 'full_name', 'email', 'company_name', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']
