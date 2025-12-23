import { useState, useRef, useEffect } from 'react';
import { Bell, X, Trash2, ExternalLink } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useNotifications } from '../../context/NotificationContext';
import notificationsApi from '../../api/services/notifications';

/**
 * NotificationBell component with dropdown panel
 * Displays notification bell icon with unread count badge and dropdown list
 * Shows only the last 3 notifications with a "View All" link
 */
const NotificationBell = () => {
    const { notifications, unreadCount, clearAll, fetchNotifications } = useNotifications();
    const [isOpen, setIsOpen] = useState(false);
    const [clearing, setClearing] = useState(false);
    const dropdownRef = useRef(null);
    const navigate = useNavigate();
    const location = useLocation();

    // Determine the notifications route based on current path
    const getNotificationsPath = () => {
        if (location.pathname.startsWith('/admin')) return '/admin/notifications';
        if (location.pathname.startsWith('/tenant-dashboard')) return '/tenant-dashboard/notifications';
        if (location.pathname.startsWith('/dev-dashboard')) return '/dev-dashboard/notifications';
        return '/notifications';
    };

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleToggle = () => {
        setIsOpen(!isOpen);
    };

    const handleClearAll = async () => {
        if (clearing) return;

        setClearing(true);
        try {
            await notificationsApi.clearAllNotifications();
            clearAll(); // Update local state
            setIsOpen(false);
        } catch (error) {
            console.error('Failed to clear notifications:', error);
        } finally {
            setClearing(false);
        }
    };

    const handleViewAll = () => {
        setIsOpen(false);
        navigate(getNotificationsPath());
    };

    const getNotificationIcon = (type) => {
        switch (type) {
            case 'repo_assigned': return '🎉';
            case 'repo_unassigned': return '📋';
            case 'member_joined': return '👋';
            case 'access_request': return '📝';
            case 'evaluation_completed': return '✅';
            case 'evaluation_failed': return '❌';
            default: return '🔔';
        }
    };

    const formatTime = (timestamp) => {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return date.toLocaleDateString();
    };

    // Show only last 3 notifications in dropdown
    const displayedNotifications = notifications.slice(0, 3);

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={handleToggle}
                className="hidden sm:flex cursor-pointer items-center justify-center rounded-full h-10 w-10 text-gray-400 hover:bg-white/10 hover:text-white transition-colors relative"
            >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 flex items-center justify-center min-w-5 h-5 px-1 text-xs font-bold text-white bg-error rounded-full animate-pulse">
                        {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                )}
            </button>

            {/* Dropdown Panel */}
            {isOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-[#0A0F16] border border-white/10 rounded-lg shadow-xl z-50 overflow-hidden">
                    {/* Header */}
                    <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                        <h3 className="text-sm font-semibold text-white">Notifications</h3>
                        <div className="flex items-center gap-2">
                            {notifications.length > 0 && (
                                <button
                                    onClick={handleClearAll}
                                    disabled={clearing}
                                    className="text-xs text-gray-400 hover:text-error flex items-center gap-1 transition-colors disabled:opacity-50"
                                >
                                    <Trash2 className="w-3 h-3" />
                                    {clearing ? 'Clearing...' : 'Clear all'}
                                </button>
                            )}
                            <button
                                onClick={() => setIsOpen(false)}
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                    </div>

                    {/* Notifications List (last 3 only) */}
                    <div className="max-h-80 overflow-y-auto">
                        {displayedNotifications.length === 0 ? (
                            <div className="px-4 py-8 text-center text-gray-500">
                                <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                <p className="text-sm">No notifications</p>
                            </div>
                        ) : (
                            displayedNotifications.map((notification) => (
                                <div
                                    key={notification.id}
                                    className="px-4 py-3 border-b border-white/5 hover:bg-white/5 transition-colors"
                                >
                                    <div className="flex items-start gap-3">
                                        <span className="text-lg">{getNotificationIcon(notification.notification_type)}</span>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-white">
                                                {notification.title}
                                            </p>
                                            <p className="text-xs text-gray-400 mt-0.5 break-words line-clamp-2">
                                                {notification.message}
                                            </p>
                                            <p className="text-xs text-gray-500 mt-1">
                                                {formatTime(notification.created_at)}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* View All Footer */}
                    {notifications.length > 0 && (
                        <div className="px-4 py-3 border-t border-white/10">
                            <button
                                onClick={handleViewAll}
                                className="w-full flex items-center justify-center gap-2 text-sm text-primary hover:text-primary/80 transition-colors"
                            >
                                <ExternalLink className="w-4 h-4" />
                                View All Notifications
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default NotificationBell;
