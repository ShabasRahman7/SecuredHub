import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Trash2, Mail, X, UserPlus } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';
import { showConfirmDialog, showSuccessToast, showErrorToast } from '../../utils/sweetAlert';

const Developers = () => {
    const { user, tenant } = useAuth();
    const [currentTenant, setCurrentTenant] = useState(null);
    const [members, setMembers] = useState([]);
    const [invites, setInvites] = useState([]);
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [resendingInvite, setResendingInvite] = useState(null);
    const [actionLoading, setActionLoading] = useState(null); // member-level loading
    const [inviteSubmitting, setInviteSubmitting] = useState(false);

    useEffect(() => {
        if (tenant) {
            setCurrentTenant(tenant);
        }
    }, [tenant]);

    useEffect(() => {
        if (currentTenant) {
            fetchMembers();
            fetchInvites();
        }
    }, [currentTenant]);

    const fetchMembers = async () => {
        if (!currentTenant) return;
        try {
            const res = await api.get(`/tenants/${currentTenant.id}/members/?include_deleted=true`);
            setMembers(res.data.members || []);
        } catch (error) {
            console.error('Failed to fetch members', error);
        }
    };

    const fetchInvites = async () => {
        if (!currentTenant) return;
        try {
            const res = await api.get(`/tenants/${currentTenant.id}/invites/`);
            setInvites(res.data.invites || []);
        } catch (error) {
            console.error("Failed to fetch invites", error);
        }
    };

    const handleInvite = async (email) => {
        try {
            const res = await api.post(`/tenants/${currentTenant.id}/invite/`, { email });
            if (res.data.success) {
                toast.success(`Invitation sent to ${email}`);
                fetchInvites();
                return true;
            }
            return false;
        } catch (error) {
            toast.error(error.response?.data?.error?.message || "Failed to send invite");
            return false;
        }
    };

    const handleResendInvite = async (inviteId) => {
        setResendingInvite(inviteId);
        try {
            const res = await api.post(`/tenants/${currentTenant.id}/invites/${inviteId}/resend/`);
            if (res.data.success) {
                toast.success(res.data.message);
                fetchInvites();
            }
        } catch (error) {
            toast.error(error.response?.data?.error?.message || "Failed to resend invite");
        } finally {
            setResendingInvite(null);
        }
    };

    const handleCancelInvite = async (inviteId) => {
        const isConfirmed = await showConfirmDialog({
            title: 'Cancel Invite?',
            text: "This invitation will be cancelled.",
            icon: 'warning'
        });
        if (!isConfirmed) return;

        try {
            const res = await api.delete(`/tenants/${currentTenant.id}/invites/${inviteId}/cancel/`);
            if (res.data.success) {
                showSuccessToast("Invitation cancelled");
                fetchInvites();
            }
        } catch (error) {
            showErrorToast("Failed to cancel invite");
        }
    };

    const handleBlockMember = async (member, block = true) => {
        if (!currentTenant) return;
        const action = block ? 'block' : 'unblock';
        const isConfirmed = await showConfirmDialog({
            title: `${block ? 'Block' : 'Unblock'} member?`,
            text: block
                ? 'This will log the member out immediately and prevent them from signing in.'
                : 'This will restore the member’s access so they can sign in again.',
            confirmButtonText: `Yes, ${action} it!`,
            cancelButtonText: 'Cancel',
            icon: block ? 'warning' : 'info'
        });
        if (!isConfirmed) return;

        setActionLoading(member.id);
        try {
            const res = await api.post(`/tenants/${currentTenant.id}/members/${member.id}/block/`, { block });
            if (res.data.success) {
                showSuccessToast(res.data.message || (block ? 'Member blocked' : 'Member unblocked'));
                setMembers(members.map(m => m.id === member.id ? { ...m, is_active: !block } : m));
            }
        } catch (error) {
            showErrorToast(error.response?.data?.error?.message || 'Failed to update member');
        } finally {
            setActionLoading(null);
        }
    };

    const handleRemoveMember = async (id) => {
        const isConfirmed = await showConfirmDialog({
            title: 'Delete Member?',
            text: "This will soft-delete the member. They will lose access immediately and their data will be scheduled for permanent deletion in 30 days. You can restore them before that.",
            confirmButtonText: 'Yes, delete it!',
            icon: 'warning'
        });
        if (!isConfirmed) return;
        setActionLoading(id);
        try {
            const res = await api.delete(`/tenants/${currentTenant.id}/members/${id}/remove/`);
            if (res.data.success) {
                showSuccessToast(res.data.message || "Member deleted. Data will be permanently removed in 30 days.");
                // refresh to update active/deleted lists
                fetchMembers();
            }
        } catch (error) {
            showErrorToast("Failed to remove member");
        } finally {
            setActionLoading(null);
        }
    };

    const handleRestoreMember = async (id) => {
        const isConfirmed = await showConfirmDialog({
            title: 'Restore Member?',
            text: "This will restore the member and re-enable their access.",
            confirmButtonText: 'Yes, restore it!',
            icon: 'info'
        });
        if (!isConfirmed) return;
        setActionLoading(id);
        try {
            const res = await api.post(`/tenants/${currentTenant.id}/members/${id}/restore/`);
            if (res.data.success) {
                showSuccessToast(res.data.message || "Member restored successfully");
                fetchMembers();
            }
        } catch (error) {
            showErrorToast(error.response?.data?.error?.message || "Failed to restore member");
        } finally {
            setActionLoading(null);
        }
    };

    const handleHardDeleteMember = async (id) => {
        const isConfirmed = await showConfirmDialog({
            title: 'Permanently Delete Member?',
            text: "This will permanently delete the member account and all associated data immediately. This action cannot be undone.",
            confirmButtonText: 'Yes, permanently delete!',
            icon: 'error'
        });
        if (!isConfirmed) return;
        setActionLoading(id);
        try {
            const res = await api.delete(`/tenants/${currentTenant.id}/members/${id}/remove/?hard_delete=true`);
            if (res.data.success) {
                showSuccessToast(res.data.message || "Member permanently deleted");
                fetchMembers();
            }
        } catch (error) {
            showErrorToast(error.response?.data?.error?.message || "Failed to permanently delete member");
        } finally {
            setActionLoading(null);
        }
    };

    if (!currentTenant) {
        return (
            <div className="h-screen flex flex-col items-center justify-center bg-[#05080C] text-white">
                <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                    <p className="text-lg">Loading tenant data...</p>
                </div>
            </div>
        );
    }

    // splitting members into active and deleted (soft-deleted) lists
    const activeMembers = members.filter(m => !m.deleted_at);
    const deletedMembers = members.filter(m => m.deleted_at);

    return (
        <>
            {/* Title Section */}
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">Team Management</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        Manage access and roles for your organization.
                    </p>
                </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3 justify-start">
                <button onClick={() => setShowInviteModal(true)} className="flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold gap-2 hover:bg-blue-600 transition-colors">
                    <UserPlus className="w-4 h-4" />
                    <span className="truncate">Invite Developer</span>
                </button>
            </div>

            {/* Active Members */}
            <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                <h3 className="text-lg font-semibold text-white">Active Members</h3>
                <div className="overflow-x-auto -mx-6">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-white/5 border-b border-white/10">
                            <tr className="text-sm text-gray-400 border-b border-white/10">
                                <th className="py-2 px-6 font-medium">Name</th>
                                <th className="py-2 px-6 font-medium">Email</th>
                                <th className="py-2 px-6 font-medium">Role / Status</th>
                                <th className="py-2 px-6 font-medium">Joined</th>
                                <th className="py-2 px-6 font-medium text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {activeMembers.map(member => (
                                <tr key={member.id} className="text-sm border-b border-white/5 text-gray-300 hover:bg-white/5 transition-colors">
                                    <td className="py-4 px-6 font-medium text-white">
                                        <div className="flex items-center gap-3">
                                            <div className="bg-primary/10 rounded-full size-8 flex items-center justify-center text-primary font-bold">
                                                {member.first_name?.[0] || 'U'}
                                            </div>
                                            <span>{member.first_name} {member.last_name}</span>
                                        </div>
                                    </td>
                                    <td className="py-4 px-6 text-gray-400">{member.email}</td>
                                    <td className="py-4 px-6">
                                        <div className="flex items-center gap-2">
                                            <span className={`px-2 py-1 rounded text-xs font-semibold ${member.role === 'owner' ? 'bg-purple-100 text-purple-800 dark:bg-purple-500/20 dark:text-purple-300' : 'bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-300'}`}>
                                                {member.role.toUpperCase()}
                                            </span>
                                            {member.role !== 'owner' && (
                                                member.is_active ? (
                                                    <span className="px-2 py-1 rounded text-xs font-semibold bg-green-500/10 text-green-300 border border-green-500/20">ACTIVE</span>
                                                ) : (
                                                    <span className="px-2 py-1 rounded text-xs font-semibold bg-red-500/10 text-red-300 border border-red-500/20">BLOCKED</span>
                                                )
                                            )}
                                        </div>
                                    </td>
                                    <td className="py-4 px-6 text-gray-400">{new Date(member.joined_at).toLocaleDateString()}</td>
                                    <td className="py-4 px-6 text-right">
                                        {member.role !== 'owner' && (
                                            <div className="flex justify-end gap-2">
                                                <button
                                                    onClick={() => handleBlockMember(member, member.is_active)}
                                                    disabled={actionLoading === member.id}
                                                    className="px-3 py-1 rounded bg-white/5 hover:bg-white/10 text-yellow-300 text-xs font-semibold disabled:opacity-50"
                                                    title={member.is_active ? 'Block' : 'Unblock'}
                                                >
                                                    {actionLoading === member.id ? <span className="loading loading-spinner loading-xs" /> : (member.is_active ? 'Block' : 'Unblock')}
                                                </button>
                                                <button
                                                    onClick={() => handleRemoveMember(member.id)}
                                                    disabled={actionLoading === member.id}
                                                    className="text-red-500 hover:bg-red-500/10 p-2 rounded transition-colors disabled:opacity-50"
                                                    title="Remove Member"
                                                >
                                                    {actionLoading === member.id ? (
                                                        <span className="loading loading-spinner loading-xs" />
                                                    ) : (
                                                        <Trash2 className="w-4 h-4" />
                                                    )}
                                                </button>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {activeMembers.length === 0 && <tr><td colSpan="5" className="py-8 text-center text-gray-500">No members found.</td></tr>}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Deleted Members (Soft-Deleted) */}
            {deletedMembers.length > 0 && (
                <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16] mt-6">
                    <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold text-white">Deleted Members</h3>
                        <span className="badge badge-sm bg-red-500/20 text-red-400 border-none">{deletedMembers.length}</span>
                    </div>
                    <div className="overflow-x-auto -mx-6">
                        <table className="w-full text-left border-collapse">
                            <thead className="bg-white/5 border-b border-white/10">
                                <tr className="text-sm text-gray-400 border-b border-white/10">
                                    <th className="py-2 px-6 font-medium">Name</th>
                                    <th className="py-2 px-6 font-medium">Email</th>
                                    <th className="py-2 px-6 font-medium">Deleted Date</th>
                                    <th className="py-2 px-6 font-medium">Hard Delete Date</th>
                                    <th className="py-2 px-6 font-medium text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {deletedMembers.map(member => (
                                    <tr key={member.id} className="text-sm border-b border-white/5 text-gray-300 hover:bg-white/5 transition-colors">
                                        <td className="py-4 px-6 font-medium text-white">
                                            <div className="flex items-center gap-3">
                                                <div className="bg-red-500/10 rounded-full size-8 flex items-center justify-center text-red-400 font-bold">
                                                    {member.first_name?.[0] || 'U'}
                                                </div>
                                                <span>{member.first_name} {member.last_name}</span>
                                            </div>
                                        </td>
                                        <td className="py-4 px-6 text-gray-400">{member.email}</td>
                                        <td className="py-4 px-6 text-gray-400">
                                            {member.deleted_at ? new Date(member.deleted_at).toLocaleDateString() : '-'}
                                        </td>
                                        <td className="py-4 px-6 text-gray-400">
                                            {member.deletion_scheduled_at ? new Date(member.deletion_scheduled_at).toLocaleDateString() : '-'}
                                        </td>
                                        <td className="py-4 px-6 text-right">
                                            <div className="flex justify-end gap-2">
                                                <button
                                                    onClick={() => handleRestoreMember(member.id)}
                                                    disabled={actionLoading === member.id}
                                                    className="px-3 py-1 rounded bg-green-500/10 hover:bg-green-500/20 text-green-300 text-xs font-semibold disabled:opacity-50"
                                                >
                                                    {actionLoading === member.id ? <span className="loading loading-spinner loading-xs" /> : 'Restore'}
                                                </button>
                                                <button
                                                    onClick={() => handleHardDeleteMember(member.id)}
                                                    disabled={actionLoading === member.id}
                                                    className="px-3 py-1 rounded bg-red-500/10 hover:bg-red-500/20 text-red-300 text-xs font-semibold disabled:opacity-50"
                                                >
                                                    {actionLoading === member.id ? <span className="loading loading-spinner loading-xs" /> : 'Delete Now'}
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

            {/* Pending Invites */}
            {invites.length > 0 && (
                <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                    <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold text-white">Pending Invitations</h3>
                        <span className="badge badge-sm bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 border-none">{invites.length}</span>
                    </div>
                    <div className="overflow-x-auto -mx-6">
                        <table className="w-full text-left border-collapse">
                            <thead className="bg-white/5 border-b border-white/10">
                                <tr className="text-sm text-gray-400 border-b border-white/10">
                                    <th className="py-2 px-6 font-medium">Email</th>
                                    <th className="py-2 px-6 font-medium">Status</th>
                                    <th className="py-2 px-6 font-medium">Sent</th>
                                    <th className="py-2 px-6 font-medium">Expires</th>
                                    <th className="py-2 px-6 font-medium text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {invites.map(invite => {
                                    const isExpired = invite.is_expired || new Date(invite.expires_at) < new Date();
                                    return (
                                        <tr key={invite.token} className="text-sm border-b border-white/5 text-gray-300 hover:bg-white/5 transition-colors">
                                            <td className="py-4 px-6 font-medium text-white">
                                                <div className="flex items-center gap-3">
                                                    <div className="bg-gray-200 dark:bg-gray-700 rounded-full size-8 flex items-center justify-center text-gray-600 dark:text-gray-300">
                                                        <Mail className="w-4 h-4" />
                                                    </div>
                                                    <span>{invite.email}</span>
                                                </div>
                                            </td>
                                            <td className="py-4 px-6">
                                                <span className={`px-2 py-1 rounded text-xs font-semibold ${isExpired
                                                    ? 'bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-300'
                                                    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-500/20 dark:text-yellow-300'
                                                }`}>
                                                    {isExpired ? 'EXPIRED' : 'PENDING'}
                                                </span>
                                            </td>
                                            <td className="py-4 px-6 text-gray-400">
                                                {new Date(invite.created_at).toLocaleDateString()}
                                            </td>
                                            <td className="py-4 px-6 text-gray-400">
                                                {new Date(invite.expires_at).toLocaleDateString()}
                                            </td>
                                            <td className="py-4 px-6 text-right">
                                                <div className="flex items-center justify-end gap-2">
                                                    {isExpired ? (
                                                        <button
                                                            onClick={() => handleResendInvite(invite.token)}
                                                            className="text-blue-500 hover:bg-blue-500/10 px-3 py-1.5 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium flex items-center gap-1"
                                                            title="Resend with new token"
                                                            disabled={resendingInvite === invite.token}
                                                        >
                                                            {resendingInvite === invite.token ? (
                                                                <>
                                                                    <span className="loading loading-spinner loading-xs"></span>
                                                                    <span>Resending...</span>
                                                                </>
                                                            ) : (
                                                                <>
                                                                    <Mail className="w-4 h-4" />
                                                                    <span>Resend</span>
                                                                </>
                                                            )}
                                                        </button>
                                                    ) : (
                                                        <span className="text-xs text-gray-500 dark:text-gray-400 italic">Waiting for acceptance</span>
                                                    )}
                                                    <button
                                                        onClick={() => handleCancelInvite(invite.token)}
                                                        className="text-red-500 hover:bg-red-500/10 p-2 rounded transition-colors"
                                                        title="Cancel invitation"
                                                    >
                                                        <X className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Invite Modal */}
            {showInviteModal && (
                <div className="modal modal-open">
                    <div className="modal-box dark:bg-[#1a1d21] border dark:border-[#282f39]">
                        <h3 className="font-bold text-lg mb-4">Invite Developer</h3>
                        <form onSubmit={async (e) => {
                            e.preventDefault();
                            if (inviteSubmitting) return;
                            setInviteSubmitting(true);
                            const formData = new FormData(e.target);
                            const email = formData.get('email');
                            const success = await handleInvite(email);
                            setInviteSubmitting(false);
                            if (success) {
                                setShowInviteModal(false);
                            }
                        }}>
                            <div className="form-control mb-4">
                                <label className="label">
                                    <span className="label-text">Email Address</span>
                                </label>
                                <input
                                    type="email"
                                    name="email"
                                    placeholder="developer@example.com"
                                    className="input input-bordered w-full dark:bg-[#101822] dark:border-[#282f39]"
                                    required
                                />
                                <label className="label">
                                    <span className="label-text-alt text-gray-500">
                                        An invitation email will be sent to this address
                                    </span>
                                </label>
                            </div>
                            <div className="modal-action">
                                <button
                                    type="button"
                                    className="btn btn-ghost"
                                    onClick={() => setShowInviteModal(false)}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="btn btn-primary bg-primary border-none disabled:opacity-50"
                                    disabled={inviteSubmitting}
                                >
                                    {inviteSubmitting ? (
                                        <span className="loading loading-spinner loading-sm" />
                                    ) : (
                                        <>
                                            <Mail className="w-4 h-4" />
                                            Send Invite
                                        </>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    );
};

export default Developers;

