import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import Sidebar from '../../components/admin/Sidebar';
import { Plus, Search, Filter, Building2, Users, ShieldCheck, Menu, Bell, HelpCircle } from 'lucide-react';
import api from '../../api/axios';
import { toast } from 'react-toastify';
import Swal from 'sweetalert2';

const Tenants = () => {
    const { user } = useAuth();
    const [tenants, setTenants] = useState([]);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('All Statuses');
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteLoading, setInviteLoading] = useState(false);

    // Modal Ref
    const addTenantModalRef = useRef(null);

    // Fetch Data
    const fetchTenants = async () => {
        setLoading(true);
        try {
            const [tenantsRes, invitesRes] = await Promise.all([
                api.get('/auth/admin/tenants/'),
                api.get('/auth/admin/tenant-invites/')
            ]);

            const activeTenants = (tenantsRes.data.tenants || []).map(t => ({ ...t, type: 'tenant', status: t.is_active ? 'Active' : 'Inactive' }));
            const invites = (invitesRes.data.unverified || []).map(i => ({
                id: i.id,
                name: i.email, // Use email as name for invites
                member_count: '-',
                repo_count: '-',
                status: 'Pending',
                last_scan: null,
                created_at: i.invited_at,
                type: 'invite',
                email: i.email
            }));

            // Merge and sort by creation date (newest first)
            const mergedData = [...invites, ...activeTenants].sort((a, b) => {
                const dateA = new Date(a.created_at || a.invited_at);
                const dateB = new Date(b.created_at || b.invited_at);
                return dateB - dateA;
            });

            setTenants(mergedData);
        } catch (error) {
            console.error('Failed to fetch data', error);
            toast.error('Failed to load tenants');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTenants();
    }, []);

    const handleInviteTenant = async (e) => {
        e.preventDefault();
        if (!inviteEmail) return;

        setInviteLoading(true);
        try {
            await api.post('/auth/admin/invite-tenant/', { email: inviteEmail });
            toast.success(`Invitation sent to ${inviteEmail}`);
            setInviteEmail('');
            addTenantModalRef.current.close();
            fetchTenants(); // Refresh list
        } catch (error) {
            toast.error(error.response?.data?.error?.message || 'Failed to send invitation');
        } finally {
            setInviteLoading(false);
        }
    };

    const handleResendInvite = async (inviteId) => {
        try {
            await api.post(`/auth/admin/tenant-invites/${inviteId}/resend/`);
            toast.success('Invitation resent successfully');
        } catch (error) {
            toast.error(error.response?.data?.error?.message || 'Failed to resend invitation');
        }
    };

    const handleDelete = async (item) => {
        const isConfirmed = await showConfirmDialog({
            title: `Delete ${item.name}?`,
            text: "This action cannot be undone.",
            confirmButtonText: 'Yes, delete it!',
            icon: 'error'
        });

        if (!isConfirmed) return;

        try {
            if (item.type === 'invite') {
                await api.delete(`/auth/admin/tenant-invites/${item.id}/delete/`);
                showSuccessToast('Invitation deleted');
            } else {
                await api.delete(`/auth/admin/tenants/${item.id}/delete/`);
                showSuccessToast('Tenant deleted');
            }
            fetchTenants();
        } catch (error) {
            showErrorToast(error.response?.data?.error?.message || 'Failed to delete');
        }
    };

    // Filtered Tenants
    const filteredTenants = tenants.filter(tenant => {
        const matchesSearch = tenant.name.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesStatus = statusFilter === 'All Statuses' || tenant.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    // Stats Calculation
    const totalTenants = tenants.filter(t => t.type === 'tenant').length;
    const activeTenantsCount = tenants.filter(t => t.status === 'Active').length;
    const totalMembers = tenants.reduce((acc, curr) => acc + (curr.member_count !== '-' ? curr.member_count : 0), 0);

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
                            <h2 className="text-lg font-bold leading-tight text-white">Tenant Management</h2>
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
                                    <h1 className="text-white text-2xl sm:text-3xl font-black leading-tight tracking-tight">Tenant Management</h1>
                                    <p className="text-gray-400 text-sm sm:text-base font-normal leading-normal">View, search, and manage all tenants on the platform.</p>
                                </div>
                            </div>
                            <button
                                onClick={() => addTenantModalRef.current.showModal()}
                                className="btn btn-primary h-10 sm:h-11 px-4 sm:px-6 rounded-lg text-sm font-medium gap-2 hover:shadow-lg hover:shadow-primary/20 border-none w-full sm:w-auto"
                            >
                                <Plus className="w-5 h-5" />
                                Add Tenant
                            </button>
                        </div>

                        {/* Stats Grid */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="flex flex-col gap-2 rounded-xl border border-white/10 bg-[#0A0F16] p-6">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-primary/10 text-primary">
                            <Building2 className="w-5 h-5" />
                        </div>
                        <p className="text-gray-400 text-base font-medium leading-normal">Total Tenants</p>
                    </div>
                    <p className="text-white tracking-tight text-3xl font-bold leading-tight">{totalTenants}</p>
                </div>
                <div className="flex flex-col gap-2 rounded-xl border border-white/10 bg-[#0A0F16] p-6">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-green-500/10 text-green-500">
                            <ShieldCheck className="w-5 h-5" />
                        </div>
                        <p className="text-gray-400 text-base font-medium leading-normal">Active Tenants</p>
                    </div>
                    <p className="text-white tracking-tight text-3xl font-bold leading-tight">{activeTenantsCount}</p>
                </div>
                <div className="flex flex-col gap-2 rounded-xl border border-white/10 bg-[#0A0F16] p-6">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-purple-500/10 text-purple-500">
                            <Users className="w-5 h-5" />
                        </div>
                        <p className="text-gray-400 text-base font-medium leading-normal">Total Members</p>
                    </div>
                    <p className="text-white tracking-tight text-3xl font-bold leading-tight">{totalMembers}</p>
                </div>
            </div>

            {/* Main Content Area with Table */}
            <div className="rounded-xl border border-white/10 bg-[#0A0F16]">
                {/* ToolBar */}
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 p-4">
                    <div className="relative w-full max-w-xs">
                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                            <Search className="w-5 h-5 text-gray-400" />
                        </div>
                        <input
                            className="block w-full rounded-lg border-white/10 bg-white/5 pl-10 text-sm text-white placeholder-gray-400 focus:border-primary focus:ring-primary"
                            placeholder="Search by name..."
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <div className="flex items-center gap-2">
                        <select
                            className="rounded-lg border-white/10 bg-white/5 text-sm text-white focus:border-primary focus:ring-primary"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                        >
                            <option>All Statuses</option>
                            <option>Active</option>
                            <option>Inactive</option>
                            <option>Pending</option>
                        </select>
                        <button className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white transition-colors">
                            <Filter className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-white/5 border-b border-white/10">
                            <tr>
                                <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Tenant Name</th>
                                <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Members</th>
                                <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Repositories</th>
                                <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Status</th>
                                <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Last Scan</th>
                                <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {loading ? (
                                <tr>
                                    <td colSpan="6" className="py-8 text-center text-gray-500">Loading tenants...</td>
                                </tr>
                            ) : filteredTenants.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="py-8 text-center text-gray-500">No tenants found.</td>
                                </tr>
                            ) : (
                                filteredTenants.map((tenant) => (
                                    <tr key={tenant.id} className="hover:bg-white/5 transition-colors">
                                        <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-white">
                                            {tenant.name}
                                            {tenant.type === 'invite' && <span className="ml-2 text-xs text-gray-500">(Invite)</span>}
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-400">{tenant.member_count}</td>
                                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-400">{tenant.repo_count}</td>
                                        <td className="whitespace-nowrap px-6 py-4 text-sm">
                                            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border ${tenant.status === 'Active'
                                                ? 'bg-green-500/10 text-green-400 border-green-500/20'
                                                : tenant.status === 'Pending'
                                                    ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                                                    : 'bg-red-500/10 text-red-400 border-red-500/20'
                                                }`}>
                                                {tenant.status}
                                            </span>
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-400">
                                            {tenant.last_scan ? new Date(tenant.last_scan).toLocaleDateString() : 'Never'}
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                                            <div className="flex items-center justify-end gap-2">
                                                {tenant.type === 'invite' ? (
                                                    <>
                                                        <button
                                                            onClick={() => handleResendInvite(tenant.id)}
                                                            className="text-primary hover:text-primary/80 transition-colors text-xs"
                                                        >
                                                            Resend
                                                        </button>
                                                        <button
                                                            onClick={() => handleDelete(tenant)}
                                                            className="text-red-500 hover:text-red-400 transition-colors text-xs"
                                                        >
                                                            Delete
                                                        </button>
                                                    </>
                                                ) : (
                                                    <button
                                                        onClick={() => handleDelete(tenant)}
                                                        className="text-red-500 hover:text-red-400 transition-colors"
                                                    >
                                                        <span className="sr-only">Delete</span>
                                                        Delete
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                <div className="flex items-center justify-between border-t border-white/10 px-4 py-3 sm:px-6">
                    <div className="flex flex-1 justify-between sm:hidden">
                        <button className="relative inline-flex items-center rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-gray-400 hover:bg-white/10">Previous</button>
                        <button className="relative ml-3 inline-flex items-center rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-gray-400 hover:bg-white/10">Next</button>
                    </div>
                    <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                        <div>
                            <p className="text-sm text-gray-400">
                                Showing <span className="font-medium text-white">1</span> to <span className="font-medium text-white">{filteredTenants.length}</span> of <span className="font-medium text-white">{totalTenants}</span> results
                            </p>
                        </div>
                        <div>
                            <nav className="isolate inline-flex -space-x-px rounded-lg shadow-sm" aria-label="Pagination">
                                <button className="relative inline-flex items-center rounded-l-lg px-2 py-2 text-gray-400 ring-1 ring-inset ring-white/10 hover:bg-white/5 focus:z-20 focus:outline-offset-0">
                                    <span className="sr-only">Previous</span>
                                    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                        <path fillRule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clipRule="evenodd" />
                                    </svg>
                                </button>
                                <button aria-current="page" className="relative z-10 inline-flex items-center bg-primary/20 px-4 py-2 text-sm font-semibold text-primary focus:z-20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">1</button>
                                <button className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-400 ring-1 ring-inset ring-white/10 hover:bg-white/5 focus:z-20 focus:outline-offset-0">2</button>
                                <button className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-400 ring-1 ring-inset ring-white/10 hover:bg-white/5 focus:z-20 focus:outline-offset-0">3</button>
                                <button className="relative inline-flex items-center rounded-r-lg px-2 py-2 text-gray-400 ring-1 ring-inset ring-white/10 hover:bg-white/5 focus:z-20 focus:outline-offset-0">
                                    <span className="sr-only">Next</span>
                                    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                        <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                                    </svg>
                                </button>
                            </nav>
                        </div>
                    </div>
                </div>
            </div>

            {/* DaisyUI Modal for Add Tenant */}
            <dialog ref={addTenantModalRef} className="modal">
                <div className="modal-box bg-[#0A0F16] border border-white/10 text-white">
                    <form method="dialog">
                        {/* if there is a button in form, it will close the modal */}
                        <button className="btn btn-sm btn-circle btn-ghost absolute right-2 top-2 text-gray-400 hover:text-white">✕</button>
                    </form>
                    <h3 className="font-bold text-lg mb-4">Invite New Tenant</h3>
                    <p className="text-gray-400 text-sm mb-6">Send an invitation email to the tenant administrator.</p>

                    <form onSubmit={handleInviteTenant}>
                        <div className="form-control w-full mb-6">
                            <label className="label">
                                <span className="label-text text-gray-300">Email Address</span>
                            </label>
                            <input
                                type="email"
                                placeholder="admin@company.com"
                                className="input input-bordered w-full bg-white/5 border-white/10 text-white focus:border-primary focus:outline-none"
                                value={inviteEmail}
                                onChange={(e) => setInviteEmail(e.target.value)}
                                required
                            />
                        </div>
                        <div className="modal-action">
                            <button
                                type="button"
                                onClick={() => addTenantModalRef.current.close()}
                                className="btn btn-ghost text-gray-400 hover:text-white mr-2"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                className="btn btn-primary text-white"
                                disabled={inviteLoading}
                            >
                                {inviteLoading ? <span className="loading loading-spinner loading-sm"></span> : 'Send Invitation'}
                            </button>
                        </div>
                    </form>
                </div>
                <form method="dialog" className="modal-backdrop">
                    <button>close</button>
                </form>
            </dialog>
                    </div>
                </main>
            </div>
        </div>
    );
};

export default Tenants;
