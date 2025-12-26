/**
 * AI Agent API service
 * Functions for interacting with the AI Compliance Agent
 */
import api from '../axios';

// AI Agent base URL - can be proxied through Django or direct
const AI_BASE_URL = import.meta.env.VITE_AI_AGENT_URL || '/ai';

/**
 * Get AI analysis for an evaluation
 * Returns prioritized recommendations with remediation steps
 * 
 * @param {Object} evaluationData - Evaluation context data
 * @param {string} evaluationData.repository_name - Repository name
 * @param {string} evaluationData.repository_url - Repository URL
 * @param {number} evaluationData.evaluation_id - Evaluation ID
 * @param {number} evaluationData.score - Current score
 * @param {string} evaluationData.grade - Letter grade (A-F)
 * @param {number} evaluationData.total_rules - Total rules count
 * @param {number} evaluationData.passed_rules - Passed rules count
 * @param {number} evaluationData.failed_rules - Failed rules count
 * @param {string} evaluationData.standard_name - Standard name
 * @param {Array} evaluationData.failures - Array of failed rules
 */
export const analyzeEvaluation = async (evaluationData, options = {}) => {
    const response = await api.post(`${AI_BASE_URL}/analyze/`, {
        evaluation: evaluationData,
        include_remediation: options.includeRemediation ?? true,
        include_framework_mapping: options.includeFrameworkMapping ?? true,
        max_recommendations: options.maxRecommendations ?? 5
    });
    return response.data;
};

/**
 * Run AI agent for a goal
 * The agent autonomously fetches data and provides analysis
 * 
 * @param {string} goal - Natural language goal
 * @param {Object} context - Optional context
 * @param {number} context.evaluationId - Evaluation ID if known
 * @param {number} context.repositoryId - Repository ID if known
 * @param {number} context.maxSteps - Max reasoning steps (1-10)
 */
export const runAgent = async (goal, context = {}) => {
    const response = await api.post(`${AI_BASE_URL}/agent/`, {
        goal,
        evaluation_id: context.evaluationId || null,
        repository_id: context.repositoryId || null,
        max_steps: context.maxSteps || 5
    });
    return response.data;
};

/**
 * Get AI recommendations for a specific evaluation by ID
 * Convenience function that fetches evaluation data and analyzes it
 * 
 * @param {number} evaluationId - Evaluation ID
 */
export const getEvaluationRecommendations = async (evaluationId) => {
    const response = await api.get(`${AI_BASE_URL}/evaluations/${evaluationId}/recommendations/`);
    return response.data;
};

/**
 * Check AI service health
 */
export const checkAIHealth = async () => {
    try {
        const response = await api.get(`${AI_BASE_URL}/health/`);
        return { available: true, ...response.data };
    } catch (error) {
        return { available: false, error: error.message };
    }
};

export default {
    analyzeEvaluation,
    runAgent,
    getEvaluationRecommendations,
    checkAIHealth
};
