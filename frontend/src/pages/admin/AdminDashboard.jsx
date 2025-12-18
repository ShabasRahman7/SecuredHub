import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import StatCard from '../../components/shared/StatCard';
import WorkerHealthCard from '../../components/shared/WorkerHealthCard';
import TableCard from '../../components/shared/TableCard';
import { Download } from 'lucide-react';
import Swal from 'sweetalert2';
import api from '../../api/axios';
import useWorkerHealth from '../../hooks/useWorkerHealth';

// High-level view of platform health, onboarding, and recent admin activity.
const AdminDashboard = () => {
    const { user } = useAuth();
    const [tenants, setTenants] = useState([]);
    const [pendingAccessRequests, setPendingAccessRequests] = useState(0);
    const [pendingTenantInvites, setPendingTenantInvites] = useState(0);
    const [loading, setLoading] = useState(true);

    const {
        data: workerHealth,
        loading: workerLoading,
        error: workerError,
    } = useWorkerHealth({ auto: true });

    // Fetch summary data for admin
    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const [tenantsRes, invitesRes, accessRes] = await Promise.all([
                    api.get('/auth/admin/tenants/'),
                    api.get('/auth/admin/tenant-invites/'),
                    api.get('/auth/admin/access-requests/'),
                ]);

                setTenants(tenantsRes.data.tenants || tenantsRes.data.results || []);
                // Tenant invites: use unverified_count as pending onboarding
                setPendingTenantInvites(invitesRes.data?.unverified_count ?? 0);
                // Access requests: count field from AdminAccessRequestListView
                setPendingAccessRequests(accessRes.data?.count ?? 0);
            } catch (error) {
                console.error('Failed to fetch admin dashboard data', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // Trigger a simple fake download flow for the platform report.
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
        <>
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

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                <StatCard
                    title="Total Tenants"
                    value={tenants.length}
                    trend={true}
                    trendValue="+2 this month"
                    trendDirection="up"
                />
                <StatCard
                    title="Pending Onboarding"
                    value={pendingTenantInvites + pendingAccessRequests}
                    subtext="Tenant invites + access requests"
                />
                <StatCard
                    title="Active Workers"
                    value={
                        workerHealth
                            ? `${workerHealth.workers?.online ?? 0} online`
                            : workerLoading
                            ? 'Loading…'
                            : '0 online'
                    }
                    trend={true}
                    trendValue={
                        workerHealth
                            ? `${workerHealth.workers?.active_tasks ?? 0} active tasks`
                            : workerError
                            ? 'Failed to load'
                            : workerLoading
                            ? 'Fetching…'
                            : '0 tasks'
                    }
                    trendDirection="up"
                />
                        </div>

            <div className="mt-6">
                <WorkerHealthCard />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
        </>
    );
};

export default AdminDashboard;
