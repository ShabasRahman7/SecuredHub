import api from '../api/axios';

export const credentialsApi = {
    // list all credentials for a tenant
    listCredentials: async (tenantId) => {
        const response = await api.get(`/tenants/${tenantId}/repositories/credentials/`);
        return response.data;
    },

    // getting specific credential details
    getCredential: async (tenantId, credentialId) => {
        const response = await api.get(`/tenants/${tenantId}/repositories/credentials/${credentialId}/`);
        return response.data;
    },

    // creating new credential
    createCredential: async (tenantId, credentialData) => {
        const response = await api.post(`/tenants/${tenantId}/repositories/credentials/create/`, credentialData);
        return response.data;
    },

    // updating credential
    updateCredential: async (tenantId, credentialId, credentialData) => {
        const response = await api.put(`/tenants/${tenantId}/repositories/credentials/${credentialId}/update/`, credentialData);
        return response.data;
    },

    // deleting credential
    deleteCredential: async (tenantId, credentialId) => {
        const response = await api.delete(`/tenants/${tenantId}/repositories/credentials/${credentialId}/delete/`);
        return response.data;
    },

    // revoke GitHub credential (also revokes on GitHub side)
    revokeGitHubCredential: async (tenantId, credentialId) => {
        const response = await api.post(`/tenants/${tenantId}/repositories/credentials/${credentialId}/revoke/`);
        return response.data;
    },

    // getting repositories from GitHub credential
    getGitHubRepositories: async (tenantId, credentialId) => {
        const response = await api.get(`/tenants/${tenantId}/repositories/credentials/${credentialId}/repositories/`);
        return response.data;
    },
};

export default credentialsApi;