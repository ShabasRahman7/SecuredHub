/**
 * Notification API Service
 * 
 * Provides functions for interacting with the notification backend endpoints.
 * 
 * Note: Notifications are auto-marked as read when fetched, so no manual
 * mark-as-read functions are needed.
 */
import api from '../axios';

/**
 * Get list of notifications for current user
 * Notifications are auto-marked as read when fetched.
 * @param {Object} options - Query options
 * @param {number} options.limit - Max notifications to return (default 50, max 100)
 */
export const getNotifications = async ({ limit = 50 } = {}) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());

    const response = await api.get(`/auth/notifications/?${params.toString()}`);
    return response.data;
};

/**
 * Get a single notification by ID (auto-marks as read)
 */
export const getNotification = async (id) => {
    const response = await api.get(`/auth/notifications/${id}/`);
    return response.data;
};

/**
 * Delete a single notification
 */
export const deleteNotification = async (id) => {
    await api.delete(`/auth/notifications/${id}/`);
};

/**
 * Clear all notifications
 */
export const clearAllNotifications = async () => {
    const response = await api.delete('/auth/notifications/clear-all/');
    return response.data;
};

/**
 * Get unread notification count
 */
export const getUnreadCount = async () => {
    const response = await api.get('/auth/notifications/unread-count/');
    return response.data;
};

export default {
    getNotifications,
    getNotification,
    deleteNotification,
    clearAllNotifications,
    getUnreadCount,
};
