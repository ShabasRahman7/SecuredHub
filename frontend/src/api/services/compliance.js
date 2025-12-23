/**
 * Compliance API service
 * Functions for interacting with the compliance evaluation endpoints
 */
import api from '../axios';

/**
 * Get list of available compliance standards
 */
export const getStandards = async () => {
    const response = await api.get('/standards/');
    return response.data;
};

/**
 * Get details of a specific standard including rules
 * @param {string} slug - Standard slug
 */
export const getStandardDetails = async (slug) => {
    const response = await api.get(`/standards/${slug}/`);
    return response.data;
};

/**
 * Get evaluations for a repository
 * @param {number} repoId - Repository ID
 */
export const getRepositoryEvaluations = async (repoId) => {
    const response = await api.get(`/compliance/repositories/${repoId}/evaluations/`);
    return response.data;
};

/**
 * Trigger a new compliance evaluation
 * @param {number} repositoryId - Repository ID
 * @param {number} standardId - Standard ID
 * @param {string} branch - Branch to evaluate (optional)
 */
export const triggerEvaluation = async (repositoryId, standardId, branch = 'main') => {
    const response = await api.post('/compliance/evaluations/trigger/', {
        repository_id: repositoryId,
        standard_id: standardId,
        branch
    });
    return response.data;
};

/**
 * Get details of a specific evaluation
 * @param {number} evaluationId - Evaluation ID
 */
export const getEvaluationDetails = async (evaluationId) => {
    const response = await api.get(`/compliance/evaluations/${evaluationId}/`);
    return response.data;
};

/**
 * Get latest evaluation for a repository + standard
 * @param {number} repoId - Repository ID
 * @param {number} standardId - Standard ID
 */
export const getLatestEvaluation = async (repoId, standardId) => {
    const response = await api.get(`/compliance/repositories/${repoId}/standards/${standardId}/latest/`);
    return response.data;
};

/**
 * Get compliance scores summary for a repository
 * @param {number} repoId - Repository ID
 */
export const getRepositoryScores = async (repoId) => {
    const response = await api.get(`/compliance/repositories/${repoId}/scores/`);
    return response.data;
};

/**
 * Get standards assigned to a repository
 * @param {number} repoId - Repository ID
 */
export const getRepositoryStandards = async (repoId) => {
    const response = await api.get(`/standards/repositories/${repoId}/`);
    return response.data;
};

/**
 * Assign a standard to a repository
 * @param {number} repoId - Repository ID
 * @param {number} standardId - Standard ID
 */
export const assignStandard = async (repoId, standardId) => {
    const response = await api.post(`/standards/repositories/${repoId}/`, {
        standard_id: standardId
    });
    return response.data;
};

/**
 * Delete an evaluation (owner only)
 * @param {number} evaluationId - Evaluation ID
 */
export const deleteEvaluation = async (evaluationId) => {
    const response = await api.delete(`/compliance/evaluations/${evaluationId}/delete/`);
    return response.data;
};

export default {
    getStandards,
    getStandardDetails,
    getRepositoryEvaluations,
    triggerEvaluation,
    getEvaluationDetails,
    getLatestEvaluation,
    getRepositoryScores,
    getRepositoryStandards,
    assignStandard,
    deleteEvaluation
};
