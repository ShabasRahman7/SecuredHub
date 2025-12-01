// Route paths constants
export const ROUTES = {
  // Public routes
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  REQUEST_ACCESS: '/request-access',
  ACCEPT_INVITE: '/accept-invite',

  // Admin routes
  ADMIN_DASHBOARD: '/admin/dashboard',
  ADMIN_TENANTS: '/admin/tenants',
  ADMIN_ACCESS_REQUESTS: '/admin/access-requests',

  // Tenant routes
  TENANT_DASHBOARD: '/tenant/dashboard',

  // Developer routes
  DEVELOPER_DASHBOARD: '/developer/dashboard',
};

export const getDefaultRoute = (user) => {
  if (!user) return ROUTES.LOGIN;
  if (user.is_superuser) return ROUTES.ADMIN_DASHBOARD;
  if (user.role === 'owner' || user.role === 'admin') return ROUTES.TENANT_DASHBOARD;
  if (user.role === 'developer') return ROUTES.DEVELOPER_DASHBOARD;
  return ROUTES.HOME;
};
