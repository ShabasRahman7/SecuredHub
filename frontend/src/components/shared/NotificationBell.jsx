import { useState, useRef, useEffect } from 'react';
import { Bell, X, Trash2 } from 'lucide-react';
import { useNotifications } from '../../context/NotificationContext';

/**
 * NotificationBell component with dropdown panel
 * Displays notification bell icon with unread count badge and dropdown list
 */
const NotificationBell = () => {
    const { notifications, unreadCount, clearAll, markAllAsRead } = useNotifications();
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

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
        // Mark all as read when opening
        if (!isOpen && unreadCount > 0) {
            markAllAsRead();
        }
    };

    const handleClearAll = () => {
        clearAll();
        setIsOpen(false);
    };

    const getNotificationIcon = (type) => {
        switch (type) {
            case 'repo_assigned': return '🎉';
            case 'repo_unassigned': return '📋';
            case 'member_joined': return '👋';
            case 'access_request': return '📝';
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
                                    className="text-xs text-gray-400 hover:text-error flex items-center gap-1 transition-colors"
                                >
                                    <Trash2 className="w-3 h-3" />
                                    Clear all
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

                    {/* Notifications List */}
                    <div className="max-h-80 overflow-y-auto">
                        {notifications.length === 0 ? (
                            <div className="px-4 py-8 text-center text-gray-500">
                                <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                <p className="text-sm">No notifications</p>
                            </div>
                        ) : (
                            notifications.map((notification) => (
                                <div
                                    key={notification.id}
                                    className="px-4 py-3 border-b border-white/5 hover:bg-white/5 transition-colors"
                                >
                                    <div className="flex items-start gap-3">
                                        <span className="text-lg">{getNotificationIcon(notification.type)}</span>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-white">
                                                {notification.title}
                                            </p>
                                            <p className="text-xs text-gray-400 mt-0.5 break-words">
                                                {notification.message}
                                            </p>
                                            <p className="text-xs text-gray-500 mt-1">
                                                {formatTime(notification.timestamp)}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default NotificationBell;
