import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Code, Shield, Bug, Bot, Settings, LogOut, UserCircle, X, Bell } from 'lucide-react';
import PropTypes from 'prop-types';
import { useNotifications } from '../../context/NotificationContext';

const DeveloperSidebar = ({ logout, user, isOpen, onClose }) => {
    const location = useLocation();
    const { unreadCount } = useNotifications();

    const menuItems = [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dev-dashboard' },
        { id: 'repositories', label: 'Repositories', icon: Code, path: '/dev-dashboard/repositories' },
        { id: 'scans', label: 'Scans', icon: Shield, path: '/dev-dashboard/scans' },
        { id: 'vulnerabilities', label: 'Vulnerabilities', icon: Bug, path: '/dev-dashboard/vulnerabilities' },
        { id: 'notifications', label: 'Notifications', icon: Bell, path: '/dev-dashboard/notifications', showBadge: true },
        { id: 'ai-assistant', label: 'AI Assistant', icon: Bot, path: '/dev-dashboard/ai-assistant' },
        { id: 'settings', label: 'Settings', icon: Settings, path: '/dev-dashboard/settings' },
    ];

    const isActive = (path) => {
        if (path === '/dev-dashboard') {
            return location.pathname === path;
        }
        return location.pathname.startsWith(path);
    };

    return (
        <>
            {/* Mobile Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/50 lg:hidden backdrop-blur-sm"
                    onClick={onClose}
                />
            )}

            <nav className={`
                fixed inset-y-0 left-0 z-50 w-64 flex flex-col bg-[#0A0F16] border-r border-white/10 transition-transform duration-300 ease-in-out
                lg:static lg:translate-x-0
                ${isOpen ? 'translate-x-0' : '-translate-x-full'}
            `}>
                <div className="flex flex-col gap-4 p-4 border-b border-white/10">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 bg-primary/20 flex items-center justify-center text-primary font-bold text-xl">
                                {user?.first_name ? user.first_name[0].toUpperCase() : 'D'}
                            </div>
                            <div className="flex flex-col">
                                <h1 className="text-white text-base font-medium leading-normal truncate w-40">
                                    SecurED-Hub
                                </h1>
                                <p className="text-gray-400 text-sm font-normal leading-normal">Developer Workspace</p>
                            </div>
                        </div>
                        {/* Mobile Close Button */}
                        <button onClick={onClose} className="lg:hidden text-gray-400 hover:text-white">
                            <X className="w-6 h-6" />
                        </button>
                    </div>
                </div>

                <div className="flex grow flex-col justify-between p-2">
                    <div className="flex flex-col gap-2">
                        {menuItems.map((item) => {
                            const Icon = item.icon;
                            const active = isActive(item.path);
                            return (
                                <Link
                                    key={item.id}
                                    to={item.path}
                                    onClick={() => onClose && onClose()}
                                    className={`flex items-center gap-3 px-3 py-2 rounded-lg w-full text-left transition-colors relative ${active
                                        ? 'bg-primary/20 text-primary'
                                        : 'text-gray-400 hover:bg-white/5 hover:text-white'
                                        }`}
                                >
                                    <Icon className={`w-5 h-5 ${active ? 'fill-current' : ''}`} />
                                    <p className="text-sm font-medium leading-normal">{item.label}</p>
                                    {item.showBadge && unreadCount > 0 && (
                                        <span className="ml-auto flex items-center justify-center min-w-5 h-5 px-1 text-xs font-bold text-white bg-error rounded-full">
                                            {unreadCount > 99 ? '99+' : unreadCount}
                                        </span>
                                    )}
                                </Link>
                            );
                        })}
                    </div>

                    <div className="flex flex-col gap-1 border-t border-white/10 pt-4">
                        <Link
                            to="/dev-dashboard/profile"
                            onClick={() => onClose && onClose()}
                            className={`flex items-center gap-3 px-3 py-2 rounded-lg w-full text-left transition-colors ${isActive('/dev-dashboard/profile')
                                ? 'bg-primary/20 text-primary'
                                : 'text-gray-400 hover:bg-white/5 hover:text-white'
                                }`}
                        >
                            <UserCircle className="w-5 h-5" />
                            <p className="text-sm font-medium leading-normal">Profile</p>
                        </Link>
                        <button
                            onClick={logout}
                            className="flex items-center gap-3 px-3 py-2 text-gray-400 hover:bg-white/5 hover:text-white rounded-lg w-full text-left transition-colors"
                        >
                            <LogOut className="w-5 h-5" />
                            <p className="text-sm font-medium leading-normal">Logout</p>
                        </button>
                    </div>
                </div>
            </nav>
        </>
    );
};

DeveloperSidebar.propTypes = {
    logout: PropTypes.func.isRequired,
    user: PropTypes.object,
    isOpen: PropTypes.bool,
    onClose: PropTypes.func
};

export default DeveloperSidebar;
