from rest_framework import serializers
from ..models import Tenant, TenantMember, MemberInvite, User


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant with user's role context."""
    role = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'description', 'created_by_email', 'role', 
                  'member_count', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        membership = TenantMember.objects.filter(
            user=request.user, 
            tenant=obj
        ).first()
        
        return membership.role if membership else None

    def get_member_count(self, obj):
        return obj.members.count()


class TenantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new tenants."""
    class Meta:
        model = Tenant
        fields = ['name', 'description']

    def create(self, validated_data):
        request = self.context.get('request')
        tenant = Tenant.objects.create(
            created_by=request.user,
            **validated_data
        )
        
        # Add creator as owner
        TenantMember.objects.create(
            tenant=tenant,
            user=request.user,
            role=TenantMember.ROLE_OWNER
        )
        
        return tenant


class TenantUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tenants."""
    class Meta:
        model = Tenant
        fields = ['name', 'description', 'is_active']


class TenantMemberSerializer(serializers.ModelSerializer):
    """Serializer for tenant members."""
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = TenantMember
        fields = ['id', 'user_id', 'email', 'first_name', 'last_name', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class InviteCreateSerializer(serializers.Serializer):
    """Serializer for creating member invitations."""
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[TenantMember.ROLE_DEVELOPER],
        default=TenantMember.ROLE_DEVELOPER
    )

    def validate_email(self, value):
        tenant = self.context.get('tenant')
        
        # Check if user is already a member
        if User.objects.filter(email=value).exists():
            user = User.objects.get(email=value)
            if TenantMember.objects.filter(tenant=tenant, user=user).exists():
                raise serializers.ValidationError("User is already a member of this tenant.")
        
        # Check for pending invite
        existing_invite = MemberInvite.objects.filter(
            tenant=tenant,
            email=value,
            status=MemberInvite.STATUS_PENDING
        ).first()
        
        if existing_invite and existing_invite.is_valid():
            raise serializers.ValidationError("An active invitation already exists for this email.")
        
        return value

    def create(self, validated_data):
        tenant = self.context.get('tenant')
        invited_by = self.context.get('invited_by')
        
        invite = MemberInvite.objects.create(
            tenant=tenant,
            email=validated_data['email'],
            role=validated_data.get('role', TenantMember.ROLE_DEVELOPER),
            invited_by=invited_by
        )
        
        return invite


class InviteSerializer(serializers.ModelSerializer):
    """Serializer for listing member invitations."""
    invited_by_email = serializers.EmailField(source='invited_by.email', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = MemberInvite
        fields = ['id', 'email', 'tenant_name', 'role', 'status', 'token',
                  'invited_by_email', 'created_at', 'expires_at', 'is_expired']
        read_only_fields = ['id', 'token', 'status', 'created_at', 'expires_at']


class AcceptInviteSerializer(serializers.Serializer):
    """Serializer for accepting invitations."""
    token = serializers.CharField()

    def validate_token(self, value):
        try:
            invite = MemberInvite.objects.get(token=value)
        except MemberInvite.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation token.")
        
        if not invite.is_valid():
            if invite.is_expired():
                raise serializers.ValidationError("This invitation has expired.")
            else:
                raise serializers.ValidationError(f"This invitation is {invite.status}.")
        
        return value
