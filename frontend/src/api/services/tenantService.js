import api from '../axios';
import { API_ENDPOINTS } from '../../constants/api';

export const tenantService = {
  // getting all tenants
  getTenants: async () => {
    const response = await api.get(API_ENDPOINTS.TENANTS);
    return response.data;
  },

  // getting tenant details
  getTenant: async (tenantId) => {
    const response = await api.get(API_ENDPOINTS.TENANT_DETAIL(tenantId));
    return response.data;
  },

  // updating tenant
  updateTenant: async (tenantId, data) => {
    const response = await api.put(API_ENDPOINTS.TENANT_UPDATE(tenantId), data);
    return response.data;
  },

  // getting tenant members
  getMembers: async (tenantId) => {
    const response = await api.get(API_ENDPOINTS.TENANT_MEMBERS(tenantId));
    return response.data;
  },

  // getting tenant repositories
  getRepositories: async (tenantId) => {
    const response = await api.get(API_ENDPOINTS.TENANT_REPOSITORIES(tenantId));
    return response.data;
  },

  // adding repository
  addRepository: async (tenantId, repoData) => {
    const response = await api.post(API_ENDPOINTS.ADD_REPOSITORY(tenantId), repoData);
    return response.data;
  },

  // deleting repository
  deleteRepository: async (tenantId, repoId) => {
    const response = await api.delete(API_ENDPOINTS.DELETE_REPOSITORY(tenantId, repoId));
    return response.data;
  },

  // assign developers to repository
  assignDevelopers: async (tenantId, repoId, developerIds) => {
    const response = await api.post(API_ENDPOINTS.ASSIGN_DEVELOPERS(tenantId, repoId), {
      developer_ids: developerIds,
    });
    return response.data;
  },
};
