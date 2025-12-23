import api from '../axios';

/**
 * Standards API Service
 * Handles all API calls related to compliance standards management
 */

// Get all available standards (built-in + custom for tenant)
export const getStandards = async (tenantId) => {
    const response = await api.get(`/standards/`, {
        params: { tenant_id: tenantId }
    });
    return response.data;
};

// Get a specific standard by slug
export const getStandard = async (slug) => {
    const response = await api.get(`/standards/${slug}/`);
    return response.data;
};

// Get rules for a specific standard by slug
export const getStandardRules = async (slug) => {
    const response = await api.get(`/standards/${slug}/rules/`);
    return response.data;
};

// Create a new custom standard (tenant-specific)
export const createStandard = async (tenantId, data) => {
    const response = await api.post(`/standards/create/`, {
        ...data,
        tenant: tenantId
    });
    return response.data;
};

// Update a custom standard
export const updateStandard = async (slug, data) => {
    const response = await api.patch(`/standards/${slug}/update/`, data);
    return response.data;
};

// Delete a custom standard
export const deleteStandard = async (slug) => {
    const response = await api.delete(`/standards/${slug}/delete/`);
    return response.data;
};

// Get standards assigned to a repository
export const getRepositoryStandards = async (repositoryId) => {
    const response = await api.get(`/standards/repositories/${repositoryId}/`);
    return response.data;
};

// Assign a standard to a repository
export const assignStandard = async (repositoryId, standardId) => {
    const response = await api.post(`/standards/repositories/${repositoryId}/`, {
        standard_id: standardId
    });
    return response.data;
};

// Remove a standard from a repository
export const removeStandard = async (repositoryId, standardId) => {
    const response = await api.delete(`/standards/repositories/${repositoryId}/${standardId}/`);
    return response.data;
};

// =====================
// Rule CRUD Functions
// =====================

// Add a rule to a custom standard
export const addRule = async (slug, ruleData) => {
    const response = await api.post(`/standards/${slug}/rules/create/`, ruleData);
    return response.data;
};

// Update a rule in a custom standard
export const updateRule = async (slug, ruleId, data) => {
    const response = await api.patch(`/standards/${slug}/rules/${ruleId}/update/`, data);
    return response.data;
};

// Delete a rule from a custom standard
export const deleteRule = async (slug, ruleId) => {
    const response = await api.delete(`/standards/${slug}/rules/${ruleId}/delete/`);
    return response.data;
};

export default {
    getStandards,
    getStandard,
    getStandardRules,
    createStandard,
    updateStandard,
    deleteStandard,
    getRepositoryStandards,
    assignStandard,
    removeStandard,
    addRule,
    updateRule,
    deleteRule
};

