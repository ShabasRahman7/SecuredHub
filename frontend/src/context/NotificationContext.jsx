import { createContext, useState, useContext, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import notificationService from '../services/notificationService';
import notificationsApi from '../api/services/notifications';
import { useAuth } from './AuthContext';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
    const { user } = useAuth();
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [isConnected, setIsConnected] = useState(false);
    const [loading, setLoading] = useState(false);

    // Fetch unread count from API (without marking as read)
    const fetchUnreadCount = useCallback(async () => {
        if (!user) return;

        try {
            const data = await notificationsApi.getUnreadCount();
            setUnreadCount(data.unread_count || 0);
        } catch (error) {
            console.error('Failed to fetch unread count:', error);
        }
    }, [user]);

    // Fetch notifications from API (marks them as read)
    const fetchNotifications = useCallback(async () => {
        if (!user) return;

        setLoading(true);
        try {
            const data = await notificationsApi.getNotifications({ limit: 50 });
            setNotifications(data.notifications || []);
            // After fetching, unread count is 0 since they're auto-marked as read
            setUnreadCount(0);
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
        } finally {
            setLoading(false);
        }
    }, [user]);

    // Connect/disconnect based on auth state
    useEffect(() => {
        const token = localStorage.getItem('access_token');

        if (user && token) {
            // Fetch unread count first (without marking as read)
            fetchUnreadCount();

            // Connect to WebSocket for real-time updates
            notificationService.connect(token);
        } else {
            // User logged out, disconnect
            notificationService.disconnect();
            setNotifications([]);
            setUnreadCount(0);
        }

        // Cleanup on unmount
        return () => {
            notificationService.disconnect();
        };
    }, [user, fetchUnreadCount]);

    // Subscribe to notification service for real-time updates
    useEffect(() => {
        const unsubscribe = notificationService.subscribe((data) => {
            if (data.type === 'connection') {
                setIsConnected(data.status === 'connected');
                return;
            }

            if (data.type === 'notification') {
                // Add real-time notification to the list
                const notification = {
                    id: data.notification_id || Date.now(),
                    notification_type: data.notification_type,
                    title: data.title,
                    message: data.message,
                    data: data.data,
                    created_at: data.timestamp,
                    is_read: false,
                };

                setNotifications(prev => {
                    // Avoid duplicates by checking notification_id
                    if (data.notification_id && prev.some(n => n.id === data.notification_id)) {
                        return prev;
                    }
                    return [notification, ...prev].slice(0, 50);
                });
                // Increment unread count for new real-time notifications
                setUnreadCount(prev => prev + 1);
            }
        });

        return unsubscribe;
    }, []);

    // Reconnect when token changes (e.g., after login)
    const reconnect = useCallback(() => {
        const token = localStorage.getItem('access_token');
        if (token) {
            notificationService.disconnect();
            notificationService.connect(token);
            fetchUnreadCount();
        }
    }, [fetchUnreadCount]);

    // Clear all notifications (local state only - API call should be separate)
    const clearAll = useCallback(() => {
        setNotifications([]);
        setUnreadCount(0);
    }, []);

    return (
        <NotificationContext.Provider value={{
            notifications,
            unreadCount,
            isConnected,
            loading,
            reconnect,
            fetchNotifications,
            fetchUnreadCount,
            clearAll,
        }}>
            {children}
        </NotificationContext.Provider>
    );
};

NotificationProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

export const useNotifications = () => useContext(NotificationContext);
