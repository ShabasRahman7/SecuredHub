import api from '../axios';
import { API_ENDPOINTS } from '../../constants/api';

export const tenantService = {
  // Get all tenants
  getTenants: async () => {
    const response = await api.get(API_ENDPOINTS.TENANTS);
    return response.data;
  },

  // Get tenant details
  getTenant: async (tenantId) => {
    const response = await api.get(API_ENDPOINTS.TENANT_DETAIL(tenantId));
    return response.data;
  },

  // Update tenant
  updateTenant: async (tenantId, data) => {
    const response = await api.put(API_ENDPOINTS.TENANT_UPDATE(tenantId), data);
    return response.data;
  },

  // Get tenant members
  getMembers: async (tenantId) => {
    const response = await api.get(API_ENDPOINTS.TENANT_MEMBERS(tenantId));
    return response.data;
  },

  // Get tenant repositories
  getRepositories: async (tenantId) => {
    const response = await api.get(API_ENDPOINTS.TENANT_REPOSITORIES(tenantId));
    return response.data;
  },

  // Add repository
  addRepository: async (tenantId, repoData) => {
    const response = await api.post(API_ENDPOINTS.ADD_REPOSITORY(tenantId), repoData);
    return response.data;
  },

  // Delete repository
  deleteRepository: async (tenantId, repoId) => {
    const response = await api.delete(API_ENDPOINTS.DELETE_REPOSITORY(tenantId, repoId));
    return response.data;
  },

  // Assign developers to repository
  assignDevelopers: async (tenantId, repoId, developerIds) => {
    const response = await api.post(API_ENDPOINTS.ASSIGN_DEVELOPERS(tenantId, repoId), {
      developer_ids: developerIds,
    });
    return response.data;
  },
};
