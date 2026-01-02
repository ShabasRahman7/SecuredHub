// routing paths constants
export const ROUTES = {
  // public routes
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  REQUEST_ACCESS: '/request-access',
  ACCEPT_INVITE: '/accept-invite',

  // admin routes
  ADMIN_DASHBOARD: '/admin/dashboard',
  ADMIN_TENANTS: '/admin/tenants',
  ADMIN_ACCESS_REQUESTS: '/admin/access-requests',

  // tenant routes
  TENANT_DASHBOARD: '/tenant/dashboard',

  // developer routes
  DEVELOPER_DASHBOARD: '/developer/dashboard',
};

export const getDefaultRoute = (user) => {
  if (!user) return ROUTES.LOGIN;
  if (user.is_superuser) return ROUTES.ADMIN_DASHBOARD;
  if (user.role === 'owner' || user.role === 'admin') return ROUTES.TENANT_DASHBOARD;
  if (user.role === 'developer') return ROUTES.DEVELOPER_DASHBOARD;
  return ROUTES.HOME;
};
