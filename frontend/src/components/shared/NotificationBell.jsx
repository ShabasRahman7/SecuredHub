import { useState, useEffect } from 'react';
import { Bell, X, Trash2 } from 'lucide-react';
import { useNotifications } from '../../context/NotificationContext';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

/**
 * NotificationBell Component
 * Displays a bell icon with unread count and dropdown showing recent notifications
 */
const NotificationBell = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const { notifications, unreadCount, markAsRead } = useNotifications();
    const [isOpen, setIsOpen] = useState(false);

    // closing dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (isOpen && !event.target.closest('.notification-dropdown')) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [isOpen]);

    // mark all unread notifications as read when dropdown opens
    useEffect(() => {
        if (isOpen && unreadCount > 0) {
            const unreadIds = notifications
                .filter(n => !n.is_read)
                .map(n => n.id);

            if (unreadIds.length > 0) {
                unreadIds.forEach(id => markAsRead(id));
            }
        }
    }, [isOpen, notifications, unreadCount, markAsRead]);

    const handleViewAll = () => {
        setIsOpen(false);

        // navigating based on user role
        if (user?.is_superuser) {
            navigate('/admin/notifications');
        } else if (user?.role === 'owner') {
            navigate('/tenant/notifications');
        } else {
            navigate('/developer/notifications');
        }
    };

    const getNotificationIcon = (type) => {
        const iconMap = {
            'repo_assigned': 'RA',
            'repo_unassigned': 'RU',
            'member_joined': 'MJ',
            'access_request': 'AR',
            'scan_complete': 'SC',
            'critical_finding': 'CF',
            'default': 'N'
        };
        return iconMap[type] || iconMap.default;
    };

    const formatTime = (timestamp) => {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;
        return date.toLocaleDateString();
    };

    // showing last 10 notifications
    const recentNotifications = notifications.slice(0, 10);

    return (
        <div className="relative notification-dropdown">
            {/* Bell Icon Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative p-2 text-gray-400 hover:text-white transition-colors"
            >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-error text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                        {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                )}
            </button>

            {isOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-[#0A0F16] border border-white/10 rounded-lg shadow-xl z-50 max-h-[500px] flex flex-col">
                    <div className="px-4 py-3 border-b border-white/10">
                        <h3 className="text-white font-semibold">Notifications</h3>
                        {unreadCount > 0 && (
                            <p className="text-xs text-gray-400 mt-1">{unreadCount} unread</p>
                        )}
                    </div>

                    {/* Notifications List */}
                    <div className="overflow-y-auto flex-1">
                        {recentNotifications.length === 0 ? (
                            <div className="px-4 py-8 text-center text-gray-500">
                                <Bell className="w-12 h-12 mx-auto mb-2 text-gray-600" />
                                <p className="text-sm">No notifications yet</p>
                            </div>
                        ) : (
                            recentNotifications.map((notification) => (
                                <div
                                    key={notification.id}
                                    className={`px-4 py-3 border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer ${!notification.is_read ? 'bg-primary/5' : ''
                                        }`}
                                    onClick={handleViewAll}
                                >
                                    <div className="flex items-start gap-2">
                                        <span className="text-lg flex-shrink-0">{getNotificationIcon(notification.notification_type)}</span>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between gap-2">
                                                <h4 className={`text-xs font-medium ${notification.is_read ? 'text-gray-300' : 'text-white'}`}>
                                                    {notification.title}
                                                </h4>
                                                {!notification.is_read && (
                                                    <span className="w-2 h-2 rounded-full bg-primary flex-shrink-0 mt-1"></span>
                                                )}
                                            </div>
                                            <p className="text-xs text-gray-400 mt-1 line-clamp-2">
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

                    {recentNotifications.length > 0 && (
                        <div className="px-4 py-3 border-t border-white/10">
                            <button
                                onClick={handleViewAll}
                                className="w-full text-center text-sm text-primary hover:text-primary/80 font-medium transition-colors"
                            >
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
