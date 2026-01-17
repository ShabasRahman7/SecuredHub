export const API_ENDPOINTS = {
  LOGIN: '/auth/login/',
  REGISTER: '/auth/register/',
  LOGOUT: '/auth/logout/',
  SEND_OTP: '/auth/send-otp/',
  VERIFY_OTP: '/auth/verify-otp/',
  RESET_PASSWORD: '/auth/reset-password/',
  REQUEST_ACCESS: '/auth/request-access/',
  VERIFY_INVITE: '/auth/verify-invite/',
  ACCEPT_INVITE: (token) => `/auth/invites/${token}/accept/`,
  PROFILE: '/auth/profile/',

  ADMIN_TENANTS: '/auth/admin/tenants/',
  ADMIN_TENANTS_WITH_DELETED: '/auth/admin/tenants/?include_deleted=true',
  ADMIN_TENANT_INVITES: '/auth/admin/tenant-invites/',
  ADMIN_INVITE_TENANT: '/auth/admin/invite-tenant/',
  ADMIN_RESEND_TENANT_INVITE: (inviteId) => `/auth/admin/tenant-invites/${inviteId}/resend/`,
  ADMIN_DELETE_TENANT_INVITE: (inviteId) => `/auth/admin/tenant-invites/${inviteId}/delete/`,
  ADMIN_DELETE_TENANT: (tenantId, hardDelete = false) =>
    `/auth/admin/tenants/${tenantId}/delete/${hardDelete ? '?hard_delete=true' : ''}`,
  ADMIN_RESTORE_TENANT: (tenantId) => `/auth/admin/tenants/${tenantId}/restore/`,
  ADMIN_BLOCK_TENANT: (tenantId) => `/auth/admin/tenants/${tenantId}/block/`,

  ADMIN_ACCESS_REQUESTS: '/auth/admin/access-requests/',
  ADMIN_APPROVE_ACCESS_REQUEST: (id) => `/auth/admin/access-requests/${id}/approve/`,
  ADMIN_REJECT_ACCESS_REQUEST: (id) => `/auth/admin/access-requests/${id}/reject/`,

  TENANTS: '/tenants/',
  TENANT_DETAIL: (id) => `/tenants/${id}/`,
  TENANT_UPDATE: (id) => `/tenants/${id}/update/`,
  TENANT_MEMBERS: (id) => `/tenants/${id}/members/`,
  TENANT_MEMBERS_WITH_DELETED: (id) => `/tenants/${id}/members/?include_deleted=true`,
  TENANT_BLOCK_MEMBER: (tenantId, memberId) => `/tenants/${tenantId}/members/${memberId}/block/`,
  TENANT_REMOVE_MEMBER: (tenantId, memberId, hardDelete = false) =>
    `/tenants/${tenantId}/members/${memberId}/remove/${hardDelete ? '?hard_delete=true' : ''}`,
  TENANT_RESTORE_MEMBER: (tenantId, memberId) => `/tenants/${tenantId}/members/${memberId}/restore/`,

  TENANT_INVITES: (id) => `/tenants/${id}/invites/`,
  TENANT_INVITE_DEVELOPER: (tenantId) => `/tenants/${tenantId}/invite/`,
  TENANT_RESEND_INVITE: (tenantId, inviteId) => `/tenants/${tenantId}/invites/${inviteId}/resend/`,
  TENANT_CANCEL_INVITE: (tenantId, inviteId) => `/tenants/${tenantId}/invites/${inviteId}/cancel/`,

  TENANT_REPOSITORIES: (id) => `/tenants/${id}/repositories/`,
  ADD_REPOSITORY: (tenantId) => `/tenants/${tenantId}/repositories/create/`,
  UNASSIGN_DEVELOPER: (tenantId, repoId, assignmentId) =>
    `/tenants/${tenantId}/repositories/${repoId}/assignments/${assignmentId}/unassign/`,

  SCAN_DETAIL: (scanId) => `/scans/${scanId}/`,
  SCAN_FINDINGS: (scanId) => `/scans/${scanId}/findings/`,
  REPOSITORY_SCANS: (repoId) => `/scans/repository/${repoId}/`,
  TRIGGER_SCAN: (repoId) => `/scans/trigger/${repoId}/`,
  DELETE_SCAN: (scanId) => `/scans/${scanId}/delete/`,

  // ============================================================================
  // cHAT / AI ASSISTANT ENDPOINTS
  // ============================================================================
  CHAT_CONVERSATIONS: '/chat/conversations',
  CHAT_INIT_FINDING: (findingId) => `/chat/findings/${findingId}/chat/init`,
  CHAT_SEND_MESSAGE: (findingId) => `/chat/findings/${findingId}/chat`,
  CHAT_DELETE_CONVERSATION: (conversationId) => `/chat/conversations/${conversationId}`,

  // ============================================================================
  // nOTIFICATIONS ENDPOINTS
  // ============================================================================
  NOTIFICATIONS: '/notifications/',
  NOTIFICATION_DETAIL: (notificationId) => `/notifications/${notificationId}/`,
  MARK_NOTIFICATIONS_READ: '/notifications/mark-read/',
  MARK_ALL_NOTIFICATIONS_READ: '/notifications/mark-all-read/',
  CLEAR_ALL_NOTIFICATIONS: '/notifications/clear-all/',
  UNREAD_NOTIFICATION_COUNT: '/notifications/unread-count/',

  // ============================================================================
  // mONITORING ENDPOINTS
  // ============================================================================
  WORKER_HEALTH: '/admin/workers/health/',
};
