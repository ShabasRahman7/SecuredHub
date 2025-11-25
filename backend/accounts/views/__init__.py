"""
Views module for accounts app.

This file imports all view functions from their respective modules,
making them available for URLs routing.

Structure:
- auth.py: Authentication views (login, register, profile, etc.)
- admin.py: Admin management views (tenant/user CRUD, invites, access requests)
- tenant.py: Tenant management views (create, update, members, invites)
- verify_invite.py: Token verification views
"""

# Authentication & User Management
from .auth import (
    register,
    login,
    logout,
    send_otp,
    verify_otp,
    reset_password,
    profile,
    admin_list_users,
    request_access
)

# Admin Management
from .admin import (
    admin_list_tenants,
    admin_delete_tenant,
    admin_update_tenant,
    admin_invite_tenant,
    list_tenant_invites,
    admin_delete_user,
    admin_update_user,
    admin_resend_tenant_invite,
    admin_delete_tenant_invite,
    admin_list_access_requests,
    admin_approve_access_request,
    admin_reject_access_request
)

# Tenant Management
from .tenant import (
    create_tenant,
    list_tenants,
    get_tenant,
    update_tenant,
    list_members,
    remove_member,
    invite_developer,
    accept_invite,
    list_invites,
    resend_invite,
    cancel_invite
)

# Invite Verification
from .verify_invite import (
    verify_tenant_invite_token,
    verify_invite_token_get
)

