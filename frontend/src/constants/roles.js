// User roles constants
export const ROLES = {
  ADMIN: 'admin',        // System admin (superuser)
  TENANT: 'owner',       // Tenant owner
  DEVELOPER: 'developer', // Developer
};

export const ROLE_LABELS = {
  [ROLES.ADMIN]: 'Admin',
  [ROLES.TENANT]: 'Tenant Owner',
  [ROLES.DEVELOPER]: 'Developer',
};

export const hasRole = (user, role) => {
  if (!user) return false;
  if (user.is_superuser) return true;
  return user.role === role;
};

export const isTenantOwner = (user) => {
  return hasRole(user, ROLES.TENANT);
};
