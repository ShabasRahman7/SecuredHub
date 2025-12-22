import { createContext, useState, useContext, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import notificationService from '../services/notificationService';
import { useAuth } from './AuthContext';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
    const { user } = useAuth();
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [isConnected, setIsConnected] = useState(false);

    // Connect/disconnect based on auth state
    useEffect(() => {
        const token = localStorage.getItem('access_token');

        if (user && token) {
            // User is logged in, connect to notifications
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
    }, [user]); // Re-run when user changes (login/logout)

    // Subscribe to notification service
    useEffect(() => {
        const unsubscribe = notificationService.subscribe((data) => {
            if (data.type === 'connection') {
                setIsConnected(data.status === 'connected');
                return;
            }

            if (data.type === 'notification') {
                const notification = {
                    id: Date.now(),
                    type: data.notification_type,
                    title: data.title,
                    message: data.message,
                    data: data.data,
                    timestamp: data.timestamp,
                    read: false,
                };

                setNotifications(prev => [notification, ...prev].slice(0, 50)); // Keep last 50
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
        }
    }, []);


    // Mark notification as read
    const markAsRead = useCallback((notificationId) => {
        setNotifications(prev =>
            prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
    }, []);

    // Mark all as read
    const markAllAsRead = useCallback(() => {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
        setUnreadCount(0);
    }, []);

    // Clear all notifications
    const clearAll = useCallback(() => {
        setNotifications([]);
        setUnreadCount(0);
    }, []);

    return (
        <NotificationContext.Provider value={{
            notifications,
            unreadCount,
            isConnected,
            reconnect,
            markAsRead,
            markAllAsRead,
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
