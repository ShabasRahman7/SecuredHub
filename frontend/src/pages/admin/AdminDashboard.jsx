import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import Sidebar from '../../components/admin/Sidebar';
import StatCard from '../../components/common/StatCard';
import ChartCard from '../../components/common/ChartCard';
import WorkerHealthCard from '../../components/admin/WorkerHealthCard';
import TableCard from '../../components/common/TableCard';
import { Download, Menu, Bell, HelpCircle } from 'lucide-react';
import Swal from 'sweetalert2';
import api from '../../api/axios';

const AdminDashboard = () => {
    const { user } = useAuth();
    const [tenants, setTenants] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sidebarOpen, setSidebarOpen] = useState(false);

    // Fetch Data
    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const res = await api.get('/auth/admin/tenants/');
                setTenants(res.data.tenants || []);
            } catch (error) {
                console.error('Failed to fetch admin data', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    const handleDownloadReport = () => {
        Swal.fire({
            title: 'Generating Report...',
            text: 'Please wait while we compile the system report.',
            background: '#0A0F16',
            color: '#fff',
            didOpen: () => {
                Swal.showLoading();
            },
            timer: 1500
        }).then(() => {
            Swal.fire({
                title: 'Report Ready!',
                text: 'System report has been downloaded successfully.',
                icon: 'success',
                customClass: {
                    popup: 'bg-[#0A0F16] border border-white/10 text-white',
                    confirmButton: 'btn btn-primary'
                }
            });
        });
    };

    return (
        <div className="flex h-screen w-full bg-[#05080C] text-white font-sans overflow-hidden">
            {/* Sidebar */}
            <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

            {/* Main Content */}
            <div className="flex flex-1 flex-col overflow-y-auto relative w-full">
                {/* Header */}
                <header className="flex sticky top-0 z-10 items-center justify-between whitespace-nowrap border-b border-white/10 px-6 py-3 bg-[#05080C]/80 backdrop-blur-sm">
                    <div className="flex items-center gap-4 lg:gap-8">
                        <button
                            className="lg:hidden p-2 -ml-2 text-gray-400 hover:text-white"
                            onClick={() => setSidebarOpen(true)}
                        >
                            <Menu className="w-6 h-6" />
                        </button>
                        <div className="flex items-center gap-3">
                            <h2 className="text-lg font-bold leading-tight text-white">Admin Dashboard</h2>
                        </div>
                    </div>
                    <div className="flex flex-1 justify-end gap-3 lg:gap-4 items-center">
                        <button className="hidden sm:flex cursor-pointer items-center justify-center rounded-full h-10 w-10 text-gray-400 hover:bg-white/10 hover:text-white transition-colors">
                            <Bell className="w-5 h-5" />
                        </button>
                        <button className="hidden sm:flex cursor-pointer items-center justify-center rounded-full h-10 w-10 text-gray-400 hover:bg-white/10 hover:text-white transition-colors">
                            <HelpCircle className="w-5 h-5" />
                        </button>
                        <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 bg-primary/20 flex items-center justify-center text-primary font-bold">
                            {user?.first_name?.[0]}
                        </div>
                    </div>
                </header>

                <main className="flex-1 p-4 lg:p-8">
                    <div className="max-w-7xl mx-auto space-y-6 lg:space-y-8">
                        {/* Title Section */}
                        <div className="flex flex-col sm:flex-row justify-between gap-4 items-start sm:items-center">
                            <div className="flex items-center gap-4">
                                <div className="flex flex-col gap-1">
                                    <h1 className="text-white text-2xl sm:text-3xl font-black leading-tight tracking-tight">Platform Admin Dashboard</h1>
                                    <p className="text-gray-400 text-sm sm:text-base font-normal leading-normal">Oversee the entire SecuredHub system</p>
                                </div>
                            </div>
                            <button
                                onClick={handleDownloadReport}
                                className="btn btn-primary h-10 sm:h-11 px-4 sm:px-6 rounded-lg text-sm font-medium gap-2 hover:shadow-lg hover:shadow-primary/20 border-none w-full sm:w-auto"
                            >
                                <Download className="w-5 h-5" />
                                Download Report
                            </button>
                        </div>

                        {/* Stats Grid */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Total Tenants"
                    value={tenants.length}
                    trend={true}
                    trendValue="+2 this month"
                    trendDirection="up"
                />
                <StatCard
                    title="Total Repositories"
                    value="1,452"
                    trend={true}
                    trendValue="+5% this month"
                    trendDirection="up"
                />
                <StatCard
                    title="RabbitMQ Queue Size"
                    value="1,204"
                    subtext="messages pending"
                />
                <StatCard
                    title="Active Workers"
                    value="48 / 50"
                    trend={true}
                    trendValue="96% capacity"
                    trendDirection="up"
                />
                        </div>

                        {/* Charts & Health Grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                <ChartCard
                    title="Scans Per Day"
                    subtitle="Last 30 days"
                    value="2,345"
                />
                <WorkerHealthCard />
                        </div>

                        {/* Tables Grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Organization Management */}
                <TableCard
                    title="Tenant Management"
                    subtitle="View and manage all tenants."
                    actionText="View All"
                    actionLink="/admin/tenants"
                >
                    <table className="w-full text-left border-collapse">
                        <thead className="border-b border-white/10 bg-white/5">
                            <tr className="text-xs text-gray-400 uppercase">
                                <th className="py-3 px-6 font-medium">Tenant</th>
                                <th className="py-3 px-6 font-medium">Members</th>
                                <th className="py-3 px-6 font-medium">Created At</th>
                                <th className="py-3 px-6 font-medium">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan="4" className="py-8 text-center text-gray-500">Loading...</td>
                                </tr>
                            ) : tenants.slice(0, 5).map((tenant) => (
                                <tr key={tenant.id} className="border-b border-white/5 text-sm text-gray-300 hover:bg-white/5 transition-colors">
                                    <td className="py-4 px-6 font-medium text-white">{tenant.name}</td>
                                    <td className="py-4 px-6">{tenant.member_count}</td>
                                    <td className="py-4 px-6">{new Date(tenant.created_at).toLocaleDateString()}</td>
                                    <td className="py-4 px-6">
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
                                            Active
                                        </span>
                                    </td>
                                </tr>
                            ))}
                            {!loading && tenants.length === 0 && (
                                <tr>
                                    <td colSpan="4" className="py-8 text-center text-gray-500">No tenants found.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </TableCard>

                {/* Recent Audit Logs */}
                <TableCard
                    title="Recent Audit Logs"
                    subtitle="Platform-wide administrative actions."
                    actionText="View All"
                    actionLink="/admin/audit-logs"
                >
                    <table className="w-full text-left border-collapse">
                        <thead className="border-b border-white/10 bg-white/5">
                            <tr className="text-xs text-gray-400 uppercase">
                                <th className="py-3 px-6 font-medium">Event</th>
                                <th className="py-3 px-6 font-medium">User</th>
                                <th className="py-3 px-6 font-medium">Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr className="border-b border-white/5 text-sm text-gray-300 hover:bg-white/5 transition-colors">
                                <td className="py-4 px-6 font-medium text-white">Org 'DataWeavers' suspended</td>
                                <td className="py-4 px-6">admin@securedhub.com</td>
                                <td className="py-4 px-6">2023-10-27 14:30</td>
                            </tr>
                            <tr className="border-b border-white/5 text-sm text-gray-300 hover:bg-white/5 transition-colors">
                                <td className="py-4 px-6 font-medium text-white">System settings updated</td>
                                <td className="py-4 px-6">admin@securedhub.com</td>
                                <td className="py-4 px-6">2023-10-27 11:15</td>
                            </tr>
                            <tr className="border-b border-white/5 text-sm text-gray-300 hover:bg-white/5 transition-colors">
                                <td className="py-4 px-6 font-medium text-white">Org 'Innovatech' owner changed</td>
                                <td className="py-4 px-6">security@securedhub.com</td>
                                <td className="py-4 px-6">2023-10-26 09:05</td>
                            </tr>
                        </tbody>
                    </table>
                </TableCard>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
};

export default AdminDashboard;
