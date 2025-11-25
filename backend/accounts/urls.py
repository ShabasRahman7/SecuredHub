from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    register, login, logout, send_otp, verify_otp, reset_password, profile,
    admin_list_tenants, admin_invite_tenant, list_tenant_invites,
    create_tenant, list_tenants, get_tenant, update_tenant, list_members, remove_member,
    invite_developer, accept_invite, list_invites, resend_invite, cancel_invite,
    verify_tenant_invite_token, verify_invite_token_get, admin_delete_tenant, admin_update_tenant,
    admin_list_users, admin_delete_user, admin_update_user,
    admin_resend_tenant_invite, admin_delete_tenant_invite,
    request_access,
    admin_list_access_requests, admin_approve_access_request, admin_reject_access_request
)


# Authentication URLs
auth_urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('profile/', profile, name='profile'),
    path('me/', profile, name='me'),  # Alias for profile endpoint
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('send-otp/', send_otp, name='send_otp'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('verify-tenant-invite/', verify_tenant_invite_token, name='verify_tenant_invite'),
    path('verify-invite/', verify_invite_token_get, name='verify_invite'),
    path('reset-password/', reset_password, name='reset_password'),
    path('request-access/', request_access, name='request_access'),
]

# Tenant URLs
tenant_urlpatterns = [
    path('tenants/', list_tenants, name='list_tenants'),
    path('tenants/create/', create_tenant, name='create_tenant'),
    path('tenants/accept-invite/', accept_invite, name='accept_invite'),
    path('tenants/<int:tenant_id>/', get_tenant, name='get_tenant'),
    path('tenants/<int:tenant_id>/update/', update_tenant, name='update_tenant'),
    path('tenants/<int:tenant_id>/members/', list_members, name='list_members'),
    path('tenants/<int:tenant_id>/members/<int:member_id>/remove/', remove_member, name='remove_member'),
    path('tenants/<int:tenant_id>/invite/', invite_developer, name='invite_developer'),
    path('tenants/<int:tenant_id>/invites/', list_invites, name='list_invites'),
    path('tenants/<int:tenant_id>/invites/<str:invite_id>/resend/', resend_invite, name='resend_invite'),
    path('tenants/<int:tenant_id>/invites/<str:invite_id>/cancel/', cancel_invite, name='cancel_invite'),
]

# Admin URLs
admin_urlpatterns = [
    path('admin/tenants/', admin_list_tenants, name='admin_list_tenants'),
    path('admin/tenants/<int:tenant_id>/delete/', admin_delete_tenant, name='admin_delete_tenant'),
    path('admin/tenants/<int:tenant_id>/update/', admin_update_tenant, name='admin_update_tenant'),
    path('admin/invite-tenant/', admin_invite_tenant, name='admin_invite_tenant'),
    path('admin/tenant-invites/', list_tenant_invites, name='list_tenant_invites'),
    path('admin/users/', admin_list_users, name='admin_list_users'),
    path('admin/users/<int:user_id>/delete/', admin_delete_user, name='admin_delete_user'),
    path('admin/users/<int:user_id>/update/', admin_update_user, name='admin_update_user'),
    path('admin/tenant-invites/<int:invite_id>/resend/', admin_resend_tenant_invite, name='admin_resend_tenant_invite'),
    path('admin/tenant-invites/<int:invite_id>/delete/', admin_delete_tenant_invite, name='admin_delete_tenant_invite'),
    path('admin/access-requests/', admin_list_access_requests, name='admin_list_access_requests'),
    path('admin/access-requests/<int:request_id>/approve/', admin_approve_access_request, name='admin_approve_access_request'),
    path('admin/access-requests/<int:request_id>/reject/', admin_reject_access_request, name='admin_reject_access_request'),
]

urlpatterns = auth_urlpatterns + tenant_urlpatterns + admin_urlpatterns
