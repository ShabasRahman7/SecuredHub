import { useState, useEffect } from 'react';
import AdminLayout from '../../components/admin/AdminLayout';
import { Check, X, Clock, Search, Shield } from 'lucide-react';
import api from '../../api/axios';
import { toast } from 'react-toastify';
import Swal from 'sweetalert2';

const AccessRequests = () => {
    const [requests, setRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchRequests();
    }, []);

    const fetchRequests = async () => {
        try {
            const response = await api.get('/auth/admin/access-requests/');
            if (response.data.success) {
                setRequests(response.data.results);
            }
        } catch (error) {
            console.error('Failed to fetch requests:', error);
            toast.error('Failed to load access requests');
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (id) => {
        const isConfirmed = await showConfirmDialog({
            title: 'Approve Request?',
            text: "An invitation email will be sent immediately.",
            confirmButtonText: 'Yes, approve it!',
            icon: 'question'
        });

        if (!isConfirmed) return;

        setActionLoading(id);
        try {
            const response = await api.post(`/auth/admin/access-requests/${id}/approve/`);
            if (response.data.success) {
                showSuccessToast(response.data.message);
                fetchRequests(); // Refresh list
            }
        } catch (error) {
            const msg = error.response?.data?.error?.message || 'Failed to approve request';
            showErrorToast(msg);
        } finally {
            setActionLoading(null);
        }
    };

    const handleReject = async (id) => {
        const isConfirmed = await showConfirmDialog({
            title: 'Reject Request?',
            text: "The user will be notified via email.",
            confirmButtonText: 'Yes, reject it!',
            icon: 'warning'
        });

        if (!isConfirmed) return;

        setActionLoading(id);
        try {
            const response = await api.post(`/auth/admin/access-requests/${id}/reject/`);
            if (response.data.success) {
                showSuccessToast('Request rejected');
                fetchRequests(); // Refresh list
            }
        } catch (error) {
            const msg = error.response?.data?.error?.message || 'Failed to reject request';
            showErrorToast(msg);
        } finally {
            setActionLoading(null);
        }
    };

    const filteredRequests = requests.filter(req =>
        req.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        req.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        req.company_name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getStatusBadge = (status) => {
        switch (status) {
            case 'approved':
                return <span className="px-2 py-1 rounded-full bg-green-500/10 text-green-500 text-xs font-medium border border-green-500/20">Approved</span>;
            case 'rejected':
                return <span className="px-2 py-1 rounded-full bg-red-500/10 text-red-500 text-xs font-medium border border-red-500/20">Rejected</span>;
            default:
                return <span className="px-2 py-1 rounded-full bg-yellow-500/10 text-yellow-500 text-xs font-medium border border-yellow-500/20">Pending</span>;
        }
    };

    return (
        <AdminLayout title="Access Requests" subtitle="Manage signup requests from the waitlist">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div></div>
                <div className="relative w-full sm:w-64">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search requests..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-[#0A0F16] border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-primary transition-colors"
                    />
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center py-12">
                    <span className="loading loading-spinner loading-lg text-primary"></span>
                </div>
            ) : (
                <div className="bg-[#0A0F16] border border-white/10 rounded-xl overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-white/10 bg-white/5">
                                    <th className="p-4 text-xs font-medium text-gray-400 uppercase">User</th>
                                    <th className="p-4 text-xs font-medium text-gray-400 uppercase">Company</th>
                                    <th className="p-4 text-xs font-medium text-gray-400 uppercase">Status</th>
                                    <th className="p-4 text-xs font-medium text-gray-400 uppercase">Date</th>
                                    <th className="p-4 text-xs font-medium text-gray-400 uppercase text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/10">
                                {filteredRequests.length === 0 ? (
                                    <tr>
                                        <td colSpan="5" className="p-8 text-center text-gray-400">
                                            No requests found
                                        </td>
                                    </tr>
                                ) : (
                                    filteredRequests.map((req) => (
                                        <tr key={req.id} className="hover:bg-white/5 transition-colors">
                                            <td className="p-4">
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-medium text-white">{req.full_name}</span>
                                                    <span className="text-xs text-gray-400">{req.email}</span>
                                                </div>
                                            </td>
                                            <td className="p-4 text-sm text-gray-300">{req.company_name}</td>
                                            <td className="p-4">{getStatusBadge(req.status)}</td>
                                            <td className="p-4 text-sm text-gray-400">
                                                {new Date(req.created_at).toLocaleDateString()}
                                            </td>
                                            <td className="p-4 text-right">
                                                {req.status === 'pending' && (
                                                    <div className="flex justify-end gap-2">
                                                        <button
                                                            onClick={() => handleApprove(req.id)}
                                                            disabled={actionLoading === req.id}
                                                            className="p-1.5 rounded-lg bg-green-500/10 text-green-500 hover:bg-green-500/20 transition-colors disabled:opacity-50"
                                                            title="Approve"
                                                        >
                                                            {actionLoading === req.id ? (
                                                                <span className="loading loading-spinner loading-xs"></span>
                                                            ) : (
                                                                <Check className="w-4 h-4" />
                                                            )}
                                                        </button>
                                                        <button
                                                            onClick={() => handleReject(req.id)}
                                                            disabled={actionLoading === req.id}
                                                            className="p-1.5 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-colors disabled:opacity-50"
                                                            title="Reject"
                                                        >
                                                            <X className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </AdminLayout>
    );
};

export default AccessRequests;
