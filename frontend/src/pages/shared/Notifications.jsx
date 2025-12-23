/**
 * Notifications Page
 * 
 * Displays all notifications with option to delete.
 * Notifications are auto-marked as read when the page is viewed.
 * Shared across all user roles.
 */
import { useState, useEffect } from 'react';
import { Bell, Trash2, RefreshCw, Loader2 } from 'lucide-react';
import { toast } from 'react-toastify';
import notificationsApi from '../../api/services/notifications';
import { useNotifications } from '../../context/NotificationContext';

const Notifications = () => {
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(null);
    const { clearAll: contextClearAll, fetchNotifications: refreshContext } = useNotifications();

    const fetchNotifications = async () => {
        setLoading(true);
        try {
            const data = await notificationsApi.getNotifications({ limit: 100 });
            setNotifications(data.notifications || []);
            // Refresh context to update header badge
            refreshContext();
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
            toast.error('Failed to load notifications');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchNotifications();
    }, []);

    const handleDelete = async (id) => {
        setActionLoading(`delete-${id}`);
        try {
            await notificationsApi.deleteNotification(id);
            setNotifications(prev => prev.filter(n => n.id !== id));
            toast.success('Notification deleted');
        } catch (error) {
            toast.error('Failed to delete notification');
        } finally {
            setActionLoading(null);
        }
    };

    const handleClearAll = async () => {
        if (!window.confirm('Are you sure you want to delete all notifications?')) return;

        setActionLoading('clear-all');
        try {
            await notificationsApi.clearAllNotifications();
            setNotifications([]);
            contextClearAll();
            toast.success('All notifications cleared');
        } catch (error) {
            toast.error('Failed to clear notifications');
        } finally {
            setActionLoading(null);
        }
    };

    const formatTime = (timestamp) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    const getTypeIcon = (type) => {
        const icons = {
            repo_assigned: '📁',
            repo_unassigned: '📤',
            member_joined: '👋',
            member_left: '👤',
            evaluation_completed: '✅',
            evaluation_failed: '❌',
            access_request: '📝',
            tenant_invite: '📧',
            system: '🔔',
        };
        return icons[type] || '🔔';
    };

    return (
        <>
            {/* Header */}
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <h1 className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight flex items-center gap-3">
                        <Bell className="w-7 h-7" />
                        Notifications
                    </h1>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        View and manage your notifications
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={fetchNotifications}
                        disabled={loading}
                        className="btn btn-ghost btn-sm gap-2"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                    {notifications.length > 0 && (
                        <button
                            onClick={handleClearAll}
                            disabled={actionLoading === 'clear-all'}
                            className="btn btn-ghost btn-sm gap-2 text-red-500"
                        >
                            {actionLoading === 'clear-all' ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Trash2 className="w-4 h-4" />
                            )}
                            Clear All
                        </button>
                    )}
                </div>
            </div>

            {/* Notification List */}
            <div className="rounded-xl border border-white/10 bg-[#0A0F16] overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    </div>
                ) : notifications.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-16 text-gray-500">
                        <Bell className="w-12 h-12 mb-4 opacity-50" />
                        <p className="text-lg font-medium">No notifications</p>
                        <p className="text-sm">You're all caught up!</p>
                    </div>
                ) : (
                    <div className="divide-y divide-white/5">
                        {notifications.map((notification) => (
                            <div
                                key={notification.id}
                                className="flex items-start gap-4 p-4 hover:bg-white/5 transition-colors"
                            >
                                {/* Icon */}
                                <div className="text-2xl flex-shrink-0 mt-1">
                                    {getTypeIcon(notification.notification_type)}
                                </div>

                                {/* Content */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-start justify-between gap-2">
                                        <h3 className="font-medium text-gray-200">
                                            {notification.title}
                                        </h3>
                                        <span className="text-xs text-gray-500 flex-shrink-0">
                                            {formatTime(notification.created_at)}
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-400 mt-1">
                                        {notification.message}
                                    </p>
                                </div>

                                {/* Delete Button */}
                                <div className="flex-shrink-0">
                                    <button
                                        onClick={() => handleDelete(notification.id)}
                                        disabled={actionLoading === `delete-${notification.id}`}
                                        className="btn btn-ghost btn-xs btn-circle text-red-500"
                                        title="Delete"
                                    >
                                        {actionLoading === `delete-${notification.id}` ? (
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                        ) : (
                                            <Trash2 className="w-4 h-4" />
                                        )}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </>
    );
};

export default Notifications;
