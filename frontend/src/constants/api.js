// API endpoints constants
export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/auth/login/',
  REGISTER: '/auth/register/',
  LOGOUT: '/auth/logout/',
  RESET_PASSWORD: '/auth/reset-password/',
  REQUEST_ACCESS: '/auth/request-access/',

  // Tenants
  TENANTS: '/tenants/',
  TENANT_UPDATE: (id) => `/tenants/${id}/update/`,
  TENANT_MEMBERS: (id) => `/tenants/${id}/members/`,
  TENANT_REPOSITORIES: (id) => `/tenants/${id}/repositories/`,
  TENANT_INVITES: (id) => `/tenants/${id}/invites/`,

  // Repositories
  ADD_REPOSITORY: (tenantId) => `/tenants/${tenantId}/repositories/create/`,

  // Monitoring
  WORKER_HEALTH: '/admin/workers/health/',
};
