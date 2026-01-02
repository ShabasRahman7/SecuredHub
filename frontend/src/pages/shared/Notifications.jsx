import { useState, useEffect } from 'react';
import { Bell, Trash2, Filter, RefreshCw } from 'lucide-react';
import { useNotifications } from '../../context/NotificationContext';
import { toast } from 'react-toastify';
import notificationAPI from '../../services/notificationAPI';
import { showConfirmDialog } from '../../utils/sweetAlert';

/**
 * Comprehensive Notifications Page
 * 
 * Features:
 * - Notification list with pagination
 * - Filtering by read/unread status
 * - Filtering by notification type
 * - Clear all with SweetAlert confirmation
 * - Auto-mark as read on click
 * - Empty states
 * - Loading and error states
 * - Mobile responsive
 */
const Notifications = () => {
    const { refresh: refreshContext } = useNotifications();
    const [notifications, setNotifications] = useState([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [isLoading, setIsLoading] = useState(false);

    // filters
    const [readFilter, setReadFilter] = useState('all'); // 'all', 'unread', 'read'
    const [typeFilter, setTypeFilter] = useState('');
    const [showFilters, setShowFilters] = useState(false);

    useEffect(() => {
        fetchNotifications();
    }, [page, readFilter, typeFilter]);

    // auto-mark all visible notifications as read
    useEffect(() => {
        if (notifications.length > 0 && !isLoading) {
            const unreadIds = notifications
                .filter(n => !n.is_read)
                .map(n => n.id);

            if (unreadIds.length > 0) {
                // mark as read after a short delay (user has viewed them)
                const timer = setTimeout(() => {
                    handleMarkAsRead(unreadIds[0]); // Will trigger for each
                    unreadIds.forEach(id => handleMarkAsRead(id));
                }, 500);

                return () => clearTimeout(timer);
            }
        }
    }, [notifications, isLoading]);

    const fetchNotifications = async () => {
        try {
            setIsLoading(true);
            const params = { page, page_size: 20 };

            if (readFilter === 'unread') params.is_read = false;
            if (readFilter === 'read') params.is_read = true;
            if (typeFilter) params.notification_type = typeFilter;

            const response = await notificationAPI.getNotifications(params);
            setNotifications(response.data.results);
            setTotalPages(Math.ceil(response.data.count / 20));
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
            toast.error('Failed to load notifications');
        } finally {
            setIsLoading(false);
        }
    };

    const handleMarkAsRead = async (notificationId) => {
        try {
            await notificationAPI.markAsRead([notificationId]);
            setNotifications(prev =>
                prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
            );
            refreshContext();
        } catch (error) {
            toast.error('Failed to mark notification as read');
        }
    };

    const handleClearAll = async () => {
        const isConfirmed = await showConfirmDialog({
            title: 'Clear All Notifications?',
            text: 'This will permanently delete all your notifications. This action cannot be undone.',
            icon: 'warning',
            confirmButtonText: 'Yes, clear all!',
            cancelButtonText: 'Cancel'
        });

        if (!isConfirmed) return;

        try {
            await notificationAPI.clearAll();
            setNotifications([]);
            refreshContext();
            toast.success('All notifications cleared');
        } catch (error) {
            toast.error('Failed to clear notifications');
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

    const notificationTypes = [
        { value: '', label: 'All Types' },
        { value: 'repo_assigned', label: 'Repository Assigned' },
        { value: 'repo_unassigned', label: 'Repository Unassigned' },
        { value: 'member_joined', label: 'Member Joined' },
        { value: 'access_request', label: 'Access Request' },
        { value: 'scan_complete', label: 'Scan Complete' },
        { value: 'critical_finding', label: 'Critical Finding' },
    ];

    return (
        <>
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                        <Bell className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">Notifications</h1>
                        <p className="text-sm text-gray-400">Manage your notifications</p>
                    </div>
                </div>
                <button
                    onClick={() => fetchNotifications()}
                    className="hidden sm:flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg transition-colors"
                >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                </button>
            </div>

            {/* Action Bar */}
            <div className="bg-[#0A0F16] border border-white/10 rounded-lg p-4 mb-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setShowFilters(!showFilters)}
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${showFilters ? 'bg-primary/20 text-primary' : 'bg-white/5 text-gray-400 hover:bg-white/10'
                                }`}
                        >
                            <Filter className="w-4 h-4" />
                            <span className="hidden sm:inline text-sm">Filters</span>
                        </button>
                    </div>
                    {notifications.length > 0 && (
                        <button
                            onClick={handleClearAll}
                            className="flex items-center gap-2 px-3 py-2 bg-error/10 hover:bg-error/20 text-error rounded-lg transition-colors"
                        >
                            <Trash2 className="w-4 h-4" />
                            <span className="text-sm">Clear All</span>
                        </button>
                    )}
                </div>

                {/* Filter Panel */}
                {showFilters && (
                    <div className="mt-4 pt-4 border-t border-white/10">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                                <label className="text-xs text-gray-400 mb-1 block">Status</label>
                                <div className="flex gap-2">
                                    {['all', 'unread', 'read'].map((filter) => (
                                        <button
                                            key={filter}
                                            onClick={() => setReadFilter(filter)}
                                            className={`flex-1 px-3 py-2 rounded-lg text-sm transition-colors ${readFilter === filter
                                                ? 'bg-primary/20 text-primary'
                                                : 'bg-white/5 text-gray-400 hover:bg-white/10'
                                                }`}
                                        >
                                            {filter.charAt(0).toUpperCase() + filter.slice(1)}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <label className="text-xs text-gray-400 mb-1 block">Type</label>
                                <select
                                    value={typeFilter}
                                    onChange={(e) => setTypeFilter(e.target.value)}
                                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                                >
                                    {notificationTypes.map((type) => (
                                        <option key={type.value} value={type.value} className="bg-[#0A0F16]">
                                            {type.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Notifications List */}
            <div className="bg-[#0A0F16] border border-white/10 rounded-lg overflow-hidden">
                {isLoading ? (
                    <div className="flex items-center justify-center py-16">
                        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                    </div>
                ) : notifications.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-16 px-4">
                        <Bell className="w-16 h-16 text-gray-600 mb-4" />
                        <h3 className="text-lg font-semibold text-white mb-2">No notifications</h3>
                        <p className="text-sm text-gray-400 text-center">
                            {readFilter === 'unread' ? "You're all caught up! No unread notifications." : "You haven't received any notifications yet."}
                        </p>
                    </div>
                ) : (
                    <>
                        {notifications.map((notification) => (
                            <div
                                key={notification.id}
                                className={`group border-b border-white/5 last:border-0 p-4 hover:bg-white/5 transition-colors ${!notification.is_read ? 'bg-primary/5' : ''
                                    }`}
                            >
                                <div className="flex items-start gap-3">
                                    <span className="text-2xl flex-shrink-0">{getNotificationIcon(notification.notification_type)}</span>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between gap-2 mb-1">
                                            <h4 className={`text-sm font-medium ${notification.is_read ? 'text-gray-300' : 'text-white'}`}>
                                                {notification.title}
                                            </h4>
                                            {!notification.is_read && (
                                                <span className="w-2 h-2 rounded-full bg-primary flex-shrink-0 mt-1"></span>
                                            )}
                                        </div>
                                        <p className="text-xs text-gray-400 break-words mb-2">
                                            {notification.message}
                                        </p>
                                        <p className="text-xs text-gray-500">
                                            {formatTime(notification.created_at)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ))}

                        {/* Pagination */}
                        {totalPages > 1 && (
                            <div className="flex items-center justify-between px-4 py-3 border-t border-white/10">
                                <button
                                    onClick={() => setPage(Math.max(1, page - 1))}
                                    disabled={page === 1}
                                    className="px-3 py-1 text-sm text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    Previous
                                </button>
                                <span className="text-sm text-gray-400">
                                    Page {page} of {totalPages}
                                </span>
                                <button
                                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                                    disabled={page === totalPages}
                                    className="px-3 py-1 text-sm text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    Next
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </>
    );
};

export default Notifications;

