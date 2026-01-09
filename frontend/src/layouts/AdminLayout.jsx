import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/navs/AdminSidebar';
import NotificationBell from '../components/shared/NotificationBell';
import { Menu, HelpCircle } from 'lucide-react';
import { Outlet } from 'react-router-dom';
import { toast } from 'react-toastify';

const AdminLayout = () => {
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const showToast = sessionStorage.getItem("showLoginToast");
    if (showToast) {
      toast.success("Login Successful!");
      sessionStorage.removeItem("showLoginToast");
    }
  }, []);

  return (
    <div className="flex h-screen w-full bg-[#05080C] text-white font-sans overflow-hidden">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

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
              <h2 className="text-lg font-bold leading-tight text-white">Admin Panel</h2>
            </div>
          </div>
          <div className="flex flex-1 justify-end gap-3 lg:gap-4 items-center">
            <NotificationBell />
            <button className="hidden sm:flex cursor-pointer items-center justify-center rounded-full h-10 w-10 text-gray-400 hover:bg-white/10 hover:text-white transition-colors">
              <HelpCircle className="w-5 h-5" />
            </button>
            <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 bg-primary/20 flex items-center justify-center text-primary font-bold">
              {user?.first_name?.[0] || 'A'}
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-6">
          <div className="space-y-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
