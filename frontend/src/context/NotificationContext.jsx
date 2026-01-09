import { createContext, useState, useContext, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import notificationService from '../services/notificationService';
import notificationAPI from '../services/notificationAPI';
import { useAuth } from './AuthContext';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
    const { user } = useAuth();
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    // fetching notifications from backend on mount
    useEffect(() => {
        if (user) {
            fetchNotifications();
            fetchUnreadCount();
        }
    }, [user]);

    const fetchNotifications = async () => {
        try {
            setIsLoading(true);
            const response = await notificationAPI.getNotifications({ page_size: 50 });
            const backendNotifications = response.data.results.map(n => ({
                id: n.id,
                notification_type: n.notification_type,
                title: n.title,
                message: n.message,
                data: n.data,
                created_at: n.created_at,
                is_read: n.is_read,
            }));
            setNotifications(backendNotifications);
        } catch (error) {
            console.error('[NotificationContext] Failed to fetch notifications:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchUnreadCount = async () => {
        try {
            const response = await notificationAPI.getUnreadCount();
            setUnreadCount(response.data.unread_count);
        } catch (error) {
            console.error('[NotificationContext] Failed to fetch unread count:', error);
        }
    };

    // connect/disconnect based on auth state
    useEffect(() => {
        const token = localStorage.getItem('access_token');

        if (user && token) {
            notificationService.connect(token);
        } else {
            notificationService.disconnect();
            setNotifications([]);
            setUnreadCount(0);
        }

        return () => {
            notificationService.disconnect();
        };
    }, [user]);

    // subscribing to notification service for real-time updates
    useEffect(() => {
        const unsubscribe = notificationService.subscribe((data) => {
            if (data.type === 'connection') {
                setIsConnected(data.status === 'connected');
                // fetching notifications when connected
                if (data.status === 'connected' && user) {
                    fetchNotifications();
                    fetchUnreadCount();
                }
                return;
            }

            if (data.type === 'notification') {
                const notification = {
                    id: Date.now(), // Temporary ID until backend sync
                    notification_type: data.notification_type,
                    title: data.title,
                    message: data.message,
                    data: data.data,
                    created_at: data.timestamp,
                    is_read: false,
                };

                setNotifications(prev => [notification, ...prev].slice(0, 50));
                setUnreadCount(prev => prev + 1);
            }
        });

        return unsubscribe;
    }, [user]);

    // reconnect when token changes
    const reconnect = useCallback(() => {
        const token = localStorage.getItem('access_token');
        if (token) {
            notificationService.disconnect();
            notificationService.connect(token);
        }
    }, []);

    // mark notification as read (sync with backend)
    const markAsRead = useCallback(async (notificationId) => {
        try {
            // optimistic update
            setNotifications(prev =>
                prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
            );
            setUnreadCount(prev => Math.max(0, prev - 1));

            // syncing with backend
            await notificationAPI.markAsRead([notificationId]);
        } catch (error) {
            console.error('[NotificationContext] Failed to mark as read:', error);
            // revert on error
            fetchNotifications();
            fetchUnreadCount();
        }
    }, []);

    // mark all as read (sync with backend)
    const markAllAsRead = useCallback(async () => {
        try {
            // optimistic update
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
            setUnreadCount(0);

            // syncing with backend
            await notificationAPI.markAllAsRead();
        } catch (error) {
            console.error('[NotificationContext] Failed to mark all as read:', error);
            // revert on error
            fetchNotifications();
            fetchUnreadCount();
        }
    }, []);

    // clearing all notifications (sync with backend)
    const clearAll = useCallback(async () => {
        try {
            // optimistic update
            setNotifications([]);
            setUnreadCount(0);

            // syncing with backend
            await notificationAPI.clearAll();
        } catch (error) {
            console.error('[NotificationContext] Failed to clear all:', error);
            // revert on error
            fetchNotifications();
            fetchUnreadCount();
        }
    }, []);

    // refresh notifications from backend
    const refresh = useCallback(() => {
        fetchNotifications();
        fetchUnreadCount();
    }, []);

    return (
        <NotificationContext.Provider value={{
            notifications,
            unreadCount,
            isConnected,
            isLoading,
            reconnect,
            markAsRead,
            markAllAsRead,
            clearAll,
            refresh,
        }}>
            {children}
        </NotificationContext.Provider>
    );
};

NotificationProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

export const useNotifications = () => useContext(NotificationContext);
