import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Building2, Activity, Bot, FileText, Settings, LogOut, Shield, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const Sidebar = ({ isOpen, onClose }) => {
    const location = useLocation();
    const { logout, user } = useAuth();

    const isActive = (path) => location.pathname === path;

    const navItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/admin-dashboard' },
        { icon: Shield, label: 'Access Requests', path: '/admin/access-requests' },
        { icon: Building2, label: 'Tenants', path: '/admin/tenants' },
        { icon: Activity, label: 'Worker Monitoring', path: '/admin/workers' },
        { icon: Bot, label: 'AI Management', path: '/admin/ai' },
        { icon: FileText, label: 'Audit Logs', path: '/admin/audit-logs' },
        { icon: Settings, label: 'Settings', path: '/admin/settings' },
    ];

    return (
        <>
            {/* Mobile Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/50 lg:hidden backdrop-blur-sm"
                    onClick={onClose}
                />
            )}

            {/* Sidebar */}
            <aside className={`
                fixed inset-y-0 left-0 z-50 w-64 flex flex-col bg-[#0A0F16] border-r border-white/10 p-4 transition-transform duration-300 ease-in-out
                lg:static lg:translate-x-0
                ${isOpen ? 'translate-x-0' : '-translate-x-full'}
            `}>
                <div className="flex items-center justify-between px-3 py-2 mb-8">
                    <div className="flex items-center gap-3">
                        <Shield className="w-8 h-8 text-primary fill-primary/20" />
                        <h1 className="text-white text-xl font-bold leading-normal">SecuredHub</h1>
                    </div>
                    {/* Close Button for Mobile */}
                    <button
                        onClick={onClose}
                        className="lg:hidden text-gray-400 hover:text-white"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <div className="flex flex-col gap-2 flex-1">
                    {navItems.map((item) => (
                        <Link
                            key={item.path}
                            to={item.path}
                            onClick={() => onClose && onClose()} // Close sidebar on mobile when link clicked
                            className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${isActive(item.path)
                                ? 'bg-primary/20 text-primary'
                                : 'text-gray-400 hover:bg-white/5 hover:text-white'
                                }`}
                        >
                            <item.icon className={`w-5 h-5 ${isActive(item.path) ? 'fill-current' : ''}`} />
                            <p className="text-sm font-medium leading-normal">{item.label}</p>
                        </Link>
                    ))}
                </div>

                <div className="mt-auto flex flex-col gap-1 border-t border-white/10 pt-4">
                    <div className="flex gap-3 items-center px-2 pb-2">
                        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                            {user?.first_name?.[0] || 'A'}
                        </div>
                        <div className="flex flex-col overflow-hidden">
                            <h1 className="text-white text-sm font-medium leading-normal truncate">{user?.first_name || 'Admin User'}</h1>
                            <p className="text-gray-400 text-xs font-normal leading-normal truncate">{user?.email || 'admin@securedhub.com'}</p>
                        </div>
                    </div>
                    <button
                        onClick={logout}
                        className="flex items-center gap-3 px-3 py-2 mt-2 text-gray-400 hover:bg-white/5 hover:text-white rounded-lg w-full text-left transition-colors"
                    >
                        <LogOut className="w-5 h-5" />
                        <p className="text-sm font-medium leading-normal">Logout</p>
                    </button>
                </div>
            </aside>
        </>
    );
};

export default Sidebar;
