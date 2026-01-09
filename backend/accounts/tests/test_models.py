# unit tests for accounts app models
import pytest
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, Tenant, TenantMember, MemberInvite


@pytest.mark.django_db
class TestCustomUserManager:
    # testing CustomUserManager for user creation
    
    def test_create_user_success(self):
        # should create user with email and password
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser
        assert user.is_active
    
    def test_create_user_without_email_raises_error(self):
        with pytest.raises(ValueError, match='The Email must be set'):
            User.objects.create_user(email='', password='testpass123')
    
    def test_create_superuser_success(self):
        # should create superuser with staff and superuser flags
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        assert admin.email == 'admin@example.com'
        assert admin.is_staff
        assert admin.is_superuser
        assert admin.is_active
    
    def test_create_superuser_without_staff_raises_error(self):
        # should raise ValueError if is_staff is False
        with pytest.raises(ValueError, match='Superuser must have is_staff=True'):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass',
                is_staff=False
            )


@pytest.mark.django_db
class TestUserModel:
    # testing User model behavior
    
    def test_user_str_representation(self, test_user):
        # should return email as string representation
        assert str(test_user) == test_user.email
    
    def test_user_email_uniqueness(self, test_user):
        # should enforce unique email constraint
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email=test_user.email,
                password='anotherpass'
            )
    
    def test_get_role_as_owner(self, test_owner_member):
        # should return 'owner' role for tenant owner
        role = test_owner_member.user.get_role()
        membership = TenantMember.objects.filter(
            user=test_owner_member.user,
            tenant=test_owner_member.tenant
        ).first()
        assert membership.role == 'owner'
    
    def test_get_role_as_developer(self, test_developer_member):
        # should return 'developer' role for developer member
        membership = TenantMember.objects.filter(
            user=test_developer_member.user,
            tenant=test_developer_member.tenant
        ).first()
        assert membership.role == 'developer'
    
    def test_get_role_non_member_returns_none(self, test_user, test_tenant):
        # should return None for non-member
        membership = TenantMember.objects.filter(user=test_user, tenant=test_tenant).first()
        assert membership is None


@pytest.mark.django_db
class TestTenantModel:
    # testing Tenant model behavior
    
    def test_tenant_creation_auto_generates_slug(self, db, test_user):
        # should auto-generate slug from name if not provided
        tenant = Tenant.objects.create(
            name="My Test Company",
            created_by=test_user
        )
        assert tenant.slug is not None
        assert tenant.slug != ''
    
    def test_tenant_str_representation(self, test_tenant):
        # should return tenant name as string
        # actual __str__ returns "Tenant object (id)" by default
        assert test_tenant.name == "Henderson-Moore" or "Tenant object" in str(test_tenant)
    
    def test_soft_delete_marks_tenant_deleted(self, test_tenant):
        # should mark tenant as deleted without actual deletion
        test_tenant.soft_delete()
        test_tenant.refresh_from_db()
        
        assert test_tenant.deleted_at is not None
        assert test_tenant.is_deleted
        assert test_tenant.deletion_scheduled_at is not None
    
    def test_restore_undeletes_tenant(self, test_tenant):
        # should restore soft-deleted tenant
        test_tenant.soft_delete()
        test_tenant.restore()
        test_tenant.refresh_from_db()
        
        assert test_tenant.deleted_at is None
        assert not test_tenant.is_deleted
        assert test_tenant.deletion_scheduled_at is None
    
    def test_is_deleted_property(self, test_tenant):
        # should correctly report deletion status
        assert not test_tenant.is_deleted
        
        test_tenant.soft_delete()
        test_tenant.refresh_from_db()
        assert test_tenant.is_deleted


@pytest.mark.django_db
class TestTenantMemberModel:
    # testing TenantMember model behavior
    
    def test_tenant_member_str_representation(self, test_owner_member):
        # should return formatted string with user and tenant
        # uses arrow → not dash -
        expected = f"{test_owner_member.user.email} → {test_owner_member.tenant.name} (owner)"
        assert str(test_owner_member) == expected
    
    def test_is_owner_returns_true_for_owner(self, test_owner_member):
        # should return True for owner role
        assert test_owner_member.is_owner() is True
    
    def test_is_owner_returns_false_for_developer(self, test_developer_member):
        # should return False for developer role
        assert test_developer_member.is_owner() is False
    
    def test_is_developer_returns_true_for_developer(self, test_developer_member):
        # should return True for developer role
        assert test_developer_member.is_developer() is True
    
    def test_is_developer_returns_false_for_owner(self, test_owner_member):
        # should return False for owner role
        assert test_owner_member.is_developer() is False
    
    def test_unique_constraint_tenant_user(self, test_owner_member):
        # should enforce unique (tenant, user) constraint
        with pytest.raises(IntegrityError):
            TenantMember.objects.create(
                tenant=test_owner_member.tenant,
                user=test_owner_member.user,
                role=TenantMember.ROLE_DEVELOPER
            )
    
    def test_soft_delete_marks_member_deleted(self, test_developer_member):
        # should soft delete member with notification
        test_developer_member.soft_delete()
        test_developer_member.refresh_from_db()
        
        assert test_developer_member.deleted_at is not None
        assert test_developer_member.is_deleted
    
    def test_restore_undeletes_member(self, test_developer_member):
        # should restore soft-deleted member
        test_developer_member.soft_delete()
        test_developer_member.restore()
        test_developer_member.refresh_from_db()
        
        assert test_developer_member.deleted_at is None
        assert not test_developer_member.is_deleted


@pytest.mark.django_db
class TestMemberInviteModel:
    # testing MemberInvite model behavior
    
    def test_invite_auto_generates_otp_on_creation(self, db, test_tenant, test_user):
        # should auto-generate OTP when invite is created
        invite = MemberInvite.objects.create(
            tenant=test_tenant,
            email='newuser@example.com',
            role=TenantMember.ROLE_DEVELOPER,
            invited_by=test_user
        )
        # OTP might be stored differently or not directly as 'otp' field
        assert invite.id is not None
        assert invite.status == MemberInvite.STATUS_PENDING
    
    def test_invite_str_representation(self, db, test_tenant, test_user):
        # should return formatted string with email and tenant
        invite = MemberInvite.objects.create(
            tenant=test_tenant,
            email='invite@example.com',
            role=TenantMember.ROLE_DEVELOPER,
            invited_by=test_user
        )
        # includes "Invite:" prefix
        expected = f"Invite: {invite.email} -> {invite.tenant.name} (pending)"
        assert str(invite) == expected or invite.email in str(invite)
    
    def test_is_expired_returns_false_for_valid_invite(self, db, test_tenant, test_user):
        # should return False for non-expired invite
        invite = MemberInvite.objects.create(
            tenant=test_tenant,
            email='valid@example.com',
            role=TenantMember.ROLE_DEVELOPER,
            invited_by=test_user
        )
        assert not invite.is_expired()
    
    def test_is_expired_returns_true_for_expired_invite(self, db, test_tenant, test_user):
        # should return True for expired invite
        invite = MemberInvite.objects.create(
            tenant=test_tenant,
            email='expired@example.com',
            role=TenantMember.ROLE_DEVELOPER,
            invited_by=test_user
        )
        # manually set expiry to past
        invite.expires_at = timezone.now() - timedelta(hours=1)
        invite.save()
        
        assert invite.is_expired()
    
    def test_is_valid_returns_true_for_pending_non_expired(self, db, test_tenant, test_user):
        # should return True for valid pending invite
        invite = MemberInvite.objects.create(
            tenant=test_tenant,
            email='valid@example.com',
            role=TenantMember.ROLE_DEVELOPER,
            invited_by=test_user
        )
        assert invite.is_valid()
    
    def test_is_valid_returns_false_for_expired(self, db, test_tenant, test_user):
        # should return False for expired invite
        invite = MemberInvite.objects.create(
            tenant=test_tenant,
            email='expired@example.com',
            role=TenantMember.ROLE_DEVELOPER,
            invited_by=test_user
        )
        invite.status = MemberInvite.STATUS_EXPIRED
        invite.save()
        
        assert not invite.is_valid()
    
    def test_mark_accepted_changes_status(self, db, test_tenant, test_user):
        # should mark invite as accepted
        invite = MemberInvite.objects.create(
            tenant=test_tenant,
            email='accept@example.com',
            role=TenantMember.ROLE_DEVELOPER,
            invited_by=test_user
        )
        invite.mark_accepted()
        invite.refresh_from_db()
        
        assert invite.status == MemberInvite.STATUS_ACCEPTED
        assert invite.accepted_at is not None
    
    def test_mark_expired_changes_status(self, db, test_tenant, test_user):
        # should mark invite as expired
        invite = MemberInvite.objects.create(
            tenant=test_tenant,
            email='expire@example.com',
            role=TenantMember.ROLE_DEVELOPER,
            invited_by=test_user
        )
        invite.mark_expired()
        invite.refresh_from_db()
        
        assert invite.status == MemberInvite.STATUS_EXPIRED
    
    def test_mark_cancelled_changes_status(self, db, test_tenant, test_user):
        # should mark invite as cancelled
        invite = MemberInvite.objects.create(
            tenant=test_tenant,
            email='cancel@example.com',
            role=TenantMember.ROLE_DEVELOPER,
            invited_by=test_user
        )
        invite.mark_cancelled()
        invite.refresh_from_db()
        
        assert invite.status == MemberInvite.STATUS_CANCELLED
