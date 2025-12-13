// API endpoints constants
export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/auth/login/',
  REGISTER: '/auth/register/',
  LOGOUT: '/auth/logout/',
  VERIFY_EMAIL: '/auth/verify-email/',
  RESEND_OTP: '/auth/resend-otp/',
  FORGOT_PASSWORD: '/auth/forgot-password/',
  RESET_PASSWORD: '/auth/reset-password/',
  REQUEST_ACCESS: '/auth/request-access/',

  // Tenants
  TENANTS: '/tenants/',
  TENANT_DETAIL: (id) => `/tenants/${id}/`,
  TENANT_UPDATE: (id) => `/tenants/${id}/update/`,
  TENANT_MEMBERS: (id) => `/tenants/${id}/members/`,
  TENANT_REPOSITORIES: (id) => `/tenants/${id}/repositories/`,
  TENANT_INVITES: (id) => `/tenants/${id}/invites/`,

  // Invites
  INVITE_DEVELOPER: (tenantId) => `/tenants/${tenantId}/invite-developer/`,
  RESEND_INVITE: (tenantId) => `/tenants/${tenantId}/resend-invite/`,
  CANCEL_INVITE: (tenantId) => `/tenants/${tenantId}/cancel-invite/`,
  VERIFY_INVITE: '/invites/verify/',
  ACCEPT_INVITE: '/invites/accept/',

  // Repositories
  ADD_REPOSITORY: (tenantId) => `/tenants/${tenantId}/repositories/create/`,
  DELETE_REPOSITORY: (tenantId, repoId) => `/tenants/${tenantId}/repositories/${repoId}/delete/`,

  // Admin
  ADMIN_TENANTS: '/admin/tenants/',
  ADMIN_INVITE_TENANT: '/admin/invite-tenant/',
  ADMIN_ACCESS_REQUESTS: '/admin/access-requests/',
  ADMIN_APPROVE_REQUEST: (id) => `/admin/access-requests/${id}/approve/`,
  ADMIN_REJECT_REQUEST: (id) => `/admin/access-requests/${id}/reject/`,
};
