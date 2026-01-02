import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import TenantSidebar from '../components/navs/TenantSidebar';
import NotificationBell from '../components/shared/NotificationBell';
import { Menu, HelpCircle, Search } from 'lucide-react';
import { Outlet, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';

const TenantLayout = () => {
  const { user, tenant, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  useEffect(() => {
    const showToast = sessionStorage.getItem("showLoginToast");
    if (showToast) {
      toast.success("Login Successful!");
      sessionStorage.removeItem("showLoginToast");
    }
  }, []);

  return (
    <div className="flex h-screen w-full bg-[#05080C] text-white font-sans overflow-hidden">
      <TenantSidebar
        logout={handleLogout}
        user={user}
        tenantName={tenant?.name}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-y-auto relative w-full">
        <header className="flex sticky top-0 z-10 items-center justify-between whitespace-nowrap border-b border-white/10 px-6 py-3 bg-[#05080C]/80 backdrop-blur-sm">
          <div className="flex items-center gap-4 lg:gap-8">
            <button
              className="lg:hidden p-2 -ml-2 text-gray-400 hover:text-white"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold leading-tight text-white">Tenant Dashboard</h2>
              {tenant?.name && (
                <div className="hidden md:flex items-center gap-2 pl-2 border-l border-white/10">
                  <span className="text-sm font-medium text-white">{tenant.name}</span>
                </div>
              )}
            </div>
            <label className="hidden md:flex flex-col min-w-40 !h-10 max-w-64">
              <div className="flex w-full flex-1 items-stretch rounded-lg h-full bg-[#0A0F16] border border-white/10">
                <div className="text-gray-400 flex items-center justify-center pl-3">
                  <Search className="w-5 h-5" />
                </div>
                <input className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg bg-transparent h-full placeholder:text-gray-500 pl-2 text-base outline-none border-none text-white" placeholder="Search" />
              </div>
            </label>
          </div>
          <div className="flex flex-1 justify-end gap-3 lg:gap-4 items-center">
            <NotificationBell />
            <button className="hidden sm:flex cursor-pointer items-center justify-center rounded-full h-10 w-10 text-gray-400 hover:bg-white/10 hover:text-white transition-colors">
              <HelpCircle className="w-5 h-5" />
            </button>
            <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 bg-primary/20 flex items-center justify-center text-primary font-bold">
              {user?.first_name?.[0] || 'T'}
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-6 lg:space-y-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default TenantLayout;

