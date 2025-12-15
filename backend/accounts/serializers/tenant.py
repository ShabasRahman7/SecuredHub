from rest_framework import serializers
from ..models import Tenant, TenantMember, TenantInvite


class TenantSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True, required=False, allow_null=True)
    deletion_scheduled_at = serializers.DateTimeField(read_only=True, required=False, allow_null=True)

    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'description', 'created_by_email', 'role', 
                  'member_count', 'created_at', 'updated_at', 'is_active', 
                  'deleted_at', 'deletion_scheduled_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'deleted_at', 'deletion_scheduled_at']
    
    def to_representation(self, instance):
        """Handle cases where deleted_at fields might not exist in database"""
        try:
            data = super().to_representation(instance)
        except Exception as e:
            # If serialization fails due to missing fields, manually build the representation
            try:
                data = {
                    'id': instance.id,
                    'name': instance.name,
                    'slug': getattr(instance, 'slug', ''),
                    'description': getattr(instance, 'description', ''),
                    'created_by_email': instance.created_by.email if instance.created_by else None,
                    'role': self.get_role(instance),
                    'member_count': self.get_member_count(instance),
                    'created_at': instance.created_at,
                    'updated_at': instance.updated_at,
                    'is_active': getattr(instance, 'is_active', True),
                    'deleted_at': None,
                    'deletion_scheduled_at': None,
                }
            except Exception:
                # If even manual building fails, return minimal data
                data = {
                    'id': instance.id,
                    'name': str(instance),
                    'slug': '',
                    'description': '',
                    'created_by_email': None,
                    'role': None,
                    'member_count': 0,
                    'created_at': None,
                    'updated_at': None,
                    'is_active': True,
                    'deleted_at': None,
                    'deletion_scheduled_at': None,
                }
        else:
            # Ensure fields exist even if they're None
            try:
                if 'deleted_at' not in data:
                    data['deleted_at'] = getattr(instance, 'deleted_at', None)
            except Exception:
                data['deleted_at'] = None
                
            try:
                if 'deletion_scheduled_at' not in data:
                    data['deletion_scheduled_at'] = getattr(instance, 'deletion_scheduled_at', None)
            except Exception:
                data['deletion_scheduled_at'] = None
        return data

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
    class Meta:
        model = Tenant
        fields = ['name', 'description']

    def create(self, validated_data):
        request = self.context.get('request')
        tenant = Tenant.objects.create(
            created_by=request.user,
            **validated_data
        )
        
        TenantMember.objects.create(
            tenant=tenant,
            user=request.user,
            role=TenantMember.ROLE_OWNER
        )
        
        return tenant


class TenantUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['name', 'description', 'is_active']


class TenantMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True, required=False, allow_null=True)
    deletion_scheduled_at = serializers.DateTimeField(read_only=True, required=False, allow_null=True)

    class Meta:
        model = TenantMember
        fields = [
            'id',
            'user_id',
            'email',
            'first_name',
            'last_name',
            'role',
            'joined_at',
            'is_active',
            'deleted_at',
            'deletion_scheduled_at',
        ]
        read_only_fields = ['id', 'joined_at', 'deleted_at', 'deletion_scheduled_at']


class TenantInviteSerializer(serializers.ModelSerializer):
    invited_by_email = serializers.EmailField(source='invited_by.email', read_only=True)
    registered_user_email = serializers.EmailField(source='registered_user.email', read_only=True, allow_null=True)
    
    class Meta:
        model = TenantInvite
        fields = ['id', 'email', 'status', 'invited_by_email', 'invited_at', 'registered_at', 'registered_user_email']
        read_only_fields = ['id', 'invited_at', 'registered_at']
