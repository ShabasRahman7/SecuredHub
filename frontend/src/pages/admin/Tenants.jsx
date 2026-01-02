import { useState, useEffect, useRef } from 'react';
import { Plus, Search, Filter, Building2, Users, ShieldCheck, RotateCcw, Trash2 } from 'lucide-react';
import api from '../../api/axios';
import { toast } from 'react-toastify';
import { showConfirmDialog, showSuccessToast, showErrorToast } from '../../utils/sweetAlert';

const Tenants = () => {
    const [currentTenants, setCurrentTenants] = useState([]);
    const [deletedTenants, setDeletedTenants] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('All Statuses');
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteLoading, setInviteLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState(null); // track current action to prevent duplicates

    // modal Ref
    const addTenantModalRef = useRef(null);

    // fetching Data
    const fetchTenants = async () => {
        setLoading(true);
        try {
            const [tenantsRes, invitesRes] = await Promise.all([
                api.get(API_ENDPOINTS.ADMIN_TENANTS_WITH_DELETED),
                api.get(API_ENDPOINTS.ADMIN_TENANT_INVITES)
            ]);

            // processing all tenants
            const allTenants = (tenantsRes.data.tenants || []).map(t => ({
                ...t,
                type: 'tenant',
                status: t.deleted_at ? 'Deleted' : (t.is_active ? 'Active' : 'Blocked')
            }));

            // separate current and deleted tenants
            const current = allTenants.filter(t => !t.deleted_at);
            const deleted = allTenants.filter(t => t.deleted_at);

            // adding invites to current tenants
            const invites = (invitesRes.data.unverified || []).map(i => ({
                id: i.id,
                name: i.email,
                member_count: '-',
                repo_count: '-',
                status: 'Pending',
                last_scan: null,
                created_at: i.invited_at,
                type: 'invite',
                email: i.email
            }));

            // merging invites with current tenants and sort
            const mergedCurrent = [...invites, ...current].sort((a, b) => {
                const dateA = new Date(a.created_at || a.invited_at);
                const dateB = new Date(b.created_at || b.invited_at);
                return dateB - dateA;
            });

            // sorting deleted tenants by deletion date (newest first)
            const sortedDeleted = deleted.sort((a, b) => {
                const dateA = new Date(a.deleted_at);
                const dateB = new Date(b.deleted_at);
                return dateB - dateA;
            });

            setCurrentTenants(mergedCurrent);
            setDeletedTenants(sortedDeleted);
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
        const key = `invite-${inviteId}-resend`;
        setActionLoading(key);
        try {
            await api.post(`/auth/admin/tenant-invites/${inviteId}/resend/`);
            toast.success('Invitation resent successfully');
        } catch (error) {
            toast.error(error.response?.data?.error?.message || 'Failed to resend invitation');
        } finally {
            setActionLoading(null);
        }
    };

    const handleDelete = async (item, isHardDelete = false) => {
        if (item.type === 'invite') {
            const isConfirmed = await showConfirmDialog({
                title: `Delete ${item.name}?`,
                text: "This action cannot be undone.",
                confirmButtonText: 'Yes, delete it!',
                icon: 'error'
            });

            if (!isConfirmed) return;

            const key = `invite-${item.id}-delete`;
            setActionLoading(key);
            try {
                await api.delete(`/auth/admin/tenant-invites/${item.id}/delete/`);
                showSuccessToast('Invitation deleted');
                fetchTenants();
            } catch (error) {
                showErrorToast(error.response?.data?.error?.message || 'Failed to delete');
            } finally {
                setActionLoading(null);
            }
            return;
        }

        // for deleted tenants: hard delete
        if (item.deleted_at || isHardDelete) {
            const isConfirmed = await showConfirmDialog({
                title: `Permanently Delete ${item.name}?`,
                text: "This will permanently delete the tenant and all its data immediately. This action cannot be undone.",
                confirmButtonText: 'Yes, permanently delete!',
                icon: 'error'
            });

            if (!isConfirmed) return;

            const key = `tenant-${item.id}-hard`;
            setActionLoading(key);
            try {
                await api.delete(`/auth/admin/tenants/${item.id}/delete/?hard_delete=true`);
                showSuccessToast('Tenant permanently deleted');
                fetchTenants();
            } catch (error) {
                showErrorToast(error.response?.data?.error?.message || 'Failed to delete');
            } finally {
                setActionLoading(null);
            }
            return;
        }

        // for current tenants: soft delete
        const isConfirmed = await showConfirmDialog({
            title: `Delete ${item.name}?`,
            text: "This will soft-delete the tenant. Data will be kept for 30 days before permanent deletion. You can restore it within this period.",
            confirmButtonText: 'Yes, delete it!',
            icon: 'warning'
        });

        if (!isConfirmed) return;

        const key = `tenant-${item.id}-soft`;
        setActionLoading(key);
        try {
            await api.delete(`/auth/admin/tenants/${item.id}/delete/`);
            showSuccessToast('Tenant deleted. Data will be permanently removed in 30 days.');
            fetchTenants();
        } catch (error) {
            showErrorToast(error.response?.data?.error?.message || 'Failed to delete');
        } finally {
            setActionLoading(null);
        }
    };

    const handleRestore = async (item) => {
        if (item.type === 'invite' || !item.deleted_at) return;

        const isConfirmed = await showConfirmDialog({
            title: `Restore ${item.name}?`,
            text: "This will restore the tenant and make it active again.",
            confirmButtonText: 'Yes, restore it!',
            icon: 'info'
        });

        if (!isConfirmed) return;

        const key = `tenant-${item.id}-restore`;
        setActionLoading(key);
        try {
            await api.post(`/auth/admin/tenants/${item.id}/restore/`);
            showSuccessToast('Tenant restored successfully');
            fetchTenants();
        } catch (error) {
            showErrorToast(error.response?.data?.error?.message || 'Failed to restore tenant');
        } finally {
            setActionLoading(null);
        }
    };

    const handleBlock = async (item) => {
        if (item.type === 'invite') return;

        const action = item.is_active ? 'block' : 'unblock';
        const isConfirmed = await showConfirmDialog({
            title: `${action.charAt(0).toUpperCase() + action.slice(1)} ${item.name}?`,
            text: action === 'block'
                ? "This will prevent the tenant and all its members from logging in."
                : "This will allow the tenant and its members to log in again.",
            confirmButtonText: `Yes, ${action} it!`,
            icon: action === 'block' ? 'warning' : 'info'
        });

        if (!isConfirmed) return;

        const key = `tenant-${item.id}-block`;
        setActionLoading(key);
        try {
            await api.post(`/auth/admin/tenants/${item.id}/block/`);
            showSuccessToast(`Tenant ${action}ed successfully`);
            fetchTenants();
        } catch (error) {
            showErrorToast(error.response?.data?.error?.message || `Failed to ${action} tenant`);
        } finally {
            setActionLoading(null);
        }
    };

    // filtered Current Tenants (excluding deleted)
    const filteredCurrentTenants = currentTenants.filter(tenant => {
        const matchesSearch = tenant.name.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesStatus = statusFilter === 'All Statuses' || tenant.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    // filtered Deleted Tenants
    const filteredDeletedTenants = deletedTenants.filter(tenant => {
        return tenant.name.toLowerCase().includes(searchQuery.toLowerCase());
    });

    // stats Calculation (only for current tenants)
    const totalTenants = currentTenants.filter(t => t.type === 'tenant').length;
    const activeTenantsCount = currentTenants.filter(t => t.status === 'Active').length;
    const totalMembers = currentTenants.reduce((acc, curr) => acc + (curr.member_count !== '-' ? curr.member_count : 0), 0);

    return (
        <>
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

            {/* Current Tenants Table */}
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
                            <option>Blocked</option>
                            <option>Pending</option>
                        </select>
                        <button className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white transition-colors">
                            <Filter className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Current Tenants Table */}
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
                            ) : filteredCurrentTenants.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="py-8 text-center text-gray-500">No tenants found.</td>
                                </tr>
                            ) : (
                                filteredCurrentTenants.map((tenant) => (
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
                                                    : tenant.status === 'Blocked'
                                                        ? 'bg-red-500/10 text-red-400 border-red-500/20'
                                                        : 'bg-gray-500/10 text-gray-400 border-gray-500/20'
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
                                                            disabled={actionLoading === `invite-${tenant.id}-resend`}
                                                            className="text-primary hover:text-primary/80 transition-colors text-xs disabled:opacity-50"
                                                        >
                                                            {actionLoading === `invite-${tenant.id}-resend` ? <span className="loading loading-spinner loading-xs" /> : 'Resend'}
                                                        </button>
                                                        <button
                                                            onClick={() => handleDelete(tenant)}
                                                            disabled={actionLoading === `invite-${tenant.id}-delete`}
                                                            className="text-red-500 hover:text-red-400 transition-colors text-xs disabled:opacity-50"
                                                        >
                                                            {actionLoading === `invite-${tenant.id}-delete` ? <span className="loading loading-spinner loading-xs" /> : 'Delete'}
                                                        </button>
                                                    </>
                                                ) : (
                                                    <>
                                                        <button
                                                            onClick={() => handleBlock(tenant)}
                                                            disabled={actionLoading === `tenant-${tenant.id}-block`}
                                                            className={`transition-colors text-xs ${tenant.is_active
                                                                    ? 'text-orange-500 hover:text-orange-400'
                                                                    : 'text-green-500 hover:text-green-400'
                                                                } disabled:opacity-50`}
                                                        >
                                                            {actionLoading === `tenant-${tenant.id}-block` ? <span className="loading loading-spinner loading-xs" /> : (tenant.is_active ? 'Block' : 'Unblock')}
                                                        </button>
                                                        <button
                                                            onClick={() => handleDelete(tenant)}
                                                            disabled={actionLoading === `tenant-${tenant.id}-soft`}
                                                            className="text-red-500 hover:text-red-400 transition-colors text-xs disabled:opacity-50"
                                                        >
                                                            {actionLoading === `tenant-${tenant.id}-soft` ? <span className="loading loading-spinner loading-xs" /> : 'Delete'}
                                                        </button>
                                                    </>
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
                    <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                        <div>
                            <p className="text-sm text-gray-400">
                                Showing <span className="font-medium text-white">1</span> to <span className="font-medium text-white">{filteredCurrentTenants.length}</span> of <span className="font-medium text-white">{totalTenants}</span> results
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Deleted Tenants Table */}
            {filteredDeletedTenants.length > 0 && (
                <div className="rounded-xl border border-white/10 bg-[#0A0F16] mt-6">
                    <div className="border-b border-white/10 p-4">
                        <h2 className="text-white text-xl font-bold">Deleted Tenants</h2>
                        <p className="text-gray-400 text-sm mt-1">Tenants scheduled for permanent deletion</p>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead className="bg-white/5 border-b border-white/10">
                                <tr>
                                    <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Tenant Name</th>
                                    <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Members</th>
                                    <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Deleted Date</th>
                                    <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Hard Delete Date</th>
                                    <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {filteredDeletedTenants.map((tenant) => (
                                    <tr key={tenant.id} className="hover:bg-white/5 transition-colors">
                                        <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-white">
                                            {tenant.name}
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-400">{tenant.member_count}</td>
                                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-400">
                                            {tenant.deleted_at ? new Date(tenant.deleted_at).toLocaleDateString() : '-'}
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-400">
                                            {tenant.deletion_scheduled_at ? new Date(tenant.deletion_scheduled_at).toLocaleDateString() : '-'}
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={() => handleRestore(tenant)}
                                                    disabled={actionLoading === `tenant-${tenant.id}-restore`}
                                                    className="text-green-500 hover:text-green-400 transition-colors text-xs flex items-center gap-1 disabled:opacity-50"
                                                    title="Restore tenant"
                                                >
                                                    {actionLoading === `tenant-${tenant.id}-restore` ? (
                                                        <span className="loading loading-spinner loading-xs" />
                                                    ) : (
                                                        <>
                                                            <RotateCcw className="w-3 h-3" />
                                                            Restore
                                                        </>
                                                    )}
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(tenant, true)}
                                                    disabled={actionLoading === `tenant-${tenant.id}-hard`}
                                                    className="text-red-500 hover:text-red-400 transition-colors text-xs flex items-center gap-1 disabled:opacity-50"
                                                    title="Permanently delete now"
                                                >
                                                    {actionLoading === `tenant-${tenant.id}-hard` ? (
                                                        <span className="loading loading-spinner loading-xs" />
                                                    ) : (
                                                        <>
                                                            <Trash2 className="w-3 h-3" />
                                                            Delete Now
                                                        </>
                                                    )}
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

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
        </>
    );
};

export default Tenants;
