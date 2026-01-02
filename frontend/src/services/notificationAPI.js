/**
 * Notification API Service
 * 
 * Provides methods to interact with the notification backend API.
 */
import api from '../api/axios';

const notificationAPI = {
    /**
     * Get list of notifications with pagination and filtering
     * @param {Object} params - Query parameters
     * @param {number} params.page - Page number
     * @param {number} params.page_size - Items per page
     * @param {boolean} params.is_read - Filter by read status
     * @param {string} params.notification_type - Filter by type
     * @returns {Promise} API response
     */
    getNotifications: async (params = {}) => {
        const queryParams = new URLSearchParams();

        if (params.page) queryParams.append('page', params.page);
        if (params.page_size) queryParams.append('page_size', params.page_size);
        if (params.is_read !== undefined) queryParams.append('is_read', params.is_read);
        if (params.notification_type) queryParams.append('notification_type', params.notification_type);

        const query = queryParams.toString();
        const url = `/notifications/${query ? `?${query}` : ''}`;

        return api.get(url);
    },

    /**
     * Get a specific notification
     * @param {number} notificationId - Notification ID
     * @returns {Promise} API response
     */
    getNotification: async (notificationId) => {
        return api.get(`/notifications/${notificationId}/`);
    },

    /**
     * Mark specific notifications as read
     * @param {Array<number>} notificationIds - Array of notification IDs
     * @returns {Promise} API response
     */
    markAsRead: async (notificationIds) => {
        return api.post('/notifications/mark-read/', {
            notification_ids: notificationIds
        });
    },

    /**
     * Mark all notifications as read
     * @returns {Promise} API response
     */
    markAllAsRead: async () => {
        return api.post('/notifications/mark-all-read/');
    },

    /**
     * Clear all notifications
     * @returns {Promise} API response
     */
    clearAll: async () => {
        return api.delete('/notifications/clear-all/');
    },

    /**
     * Get unread notification count
     * @returns {Promise} API response with {unread_count: number}
     */
    getUnreadCount: async () => {
        return api.get('/notifications/unread-count/');
    }
};

export default notificationAPI;
