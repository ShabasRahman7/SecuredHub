import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Shield, Clock, CheckCircle, XCircle, AlertCircle, Trash2, RefreshCw } from 'lucide-react';
import { toast } from 'react-toastify';
import Swal from 'sweetalert2';
import api from '../../api/axios';

const Scans = () => {
    const { tenant } = useAuth();
    const navigate = useNavigate();
    const [scans, setScans] = useState([]);
    const [loading, setLoading] = useState(false);
    const [deleting, setDeleting] = useState(null);

    useEffect(() => {
        fetchScans();
    }, [tenant]);

    const fetchScans = async () => {
        if (!tenant) return;
        setLoading(true);
        try {
            const reposRes = await api.get(`/tenants/${tenant.id}/repositories/`);
            const repos = reposRes.data.repositories || [];

            const allScans = [];
            for (const repo of repos) {
                try {
                    const scansRes = await api.get(`/scans/repository/${repo.id}/`);
                    const repoScans = (scansRes.data || []).map(s => ({
                        ...s,
                        repository_name: repo.name,
                        repository_id: repo.id
                    }));
                    allScans.push(...repoScans);
                } catch (err) {
                    console.error(`Failed to fetch scans for ${repo.name}:`, err);
                }
            }

            allScans.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            setScans(allScans);
        } catch (error) {
            toast.error('Failed to load scans');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteScan = async (scan) => {
        const result = await Swal.fire({
            title: 'Delete Scan?',
            html: `
                <p>Are you sure you want to delete this scan?</p>
                <p class="text-sm text-gray-500 mt-2">Repository: <strong>${scan.repository_name}</strong></p>
                <p class="text-sm text-gray-500">Scan ID: <strong>${scan.id}</strong></p>
                <p class="text-sm text-red-400 mt-3">Warning: This will delete all findings for this scan.</p>
            `,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#ef4444',
            cancelButtonColor: '#6b7280',
            confirmButtonText: 'Yes, delete it!',
            cancelButtonText: 'Cancel',
            background: '#0A0F16',
            color: '#fff',
            customClass: {
                popup: 'border border-white/10'
            }
        });

        if (result.isConfirmed) {
            try {
                setDeleting(scan.id);
                await api.delete(`/scans/${scan.id}/delete/`);
                toast.success('Scan deleted successfully');
                fetchScans();
            } catch (error) {
                toast.error(error.response?.data?.error || 'Failed to delete scan');
            } finally {
                setDeleting(null);
            }
        }
    };

    const getStatusConfig = (status) => {
        switch (status) {
            case 'completed':
                return {
                    icon: CheckCircle,
                    text: 'Completed',
                    className: 'bg-green-500/10 text-green-400 border-green-500/20'
                };
            case 'failed':
                return {
                    icon: XCircle,
                    text: 'Failed',
                    className: 'bg-red-500/10 text-red-400 border-red-500/20'
                };
            case 'running':
                return {
                    icon: Clock,
                    text: 'Running',
                    className: 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                };
            case 'queued':
                return {
                    icon: Clock,
                    text: 'Queued',
                    className: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                };
            default:
                return {
                    icon: AlertCircle,
                    text: status,
                    className: 'bg-gray-500/10 text-gray-400 border-gray-500/20'
                };
        }
    };

    return (
        <>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
                <div className="flex-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight text-white">Scans</p>
                    <p className="text-gray-400 text-sm lg:text-base font-normal mt-1">
                        Manage all security scans across tenant repositories
                    </p>
                </div>
                <button
                    onClick={fetchScans}
                    disabled={loading}
                    className="btn btn-sm bg-primary hover:bg-primary/80 border-none text-white gap-2"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                </button>
            </div>

            {loading && (
                <div className="flex items-center justify-center py-12">
                    <span className="loading loading-spinner loading-lg text-primary"></span>
                </div>
            )}

            {!loading && (
                <div className="bg-[#0A0F16] shadow-xl rounded-xl border border-white/10 overflow-hidden">
                    <div className="p-6 border-b border-white/10">
                        <h2 className="text-xl font-bold flex items-center text-white gap-2">
                            <Shield className="w-5 h-5" />
                            All Scans
                            <span className="ml-2 px-2 py-0.5 bg-primary/20 text-primary text-sm font-semibold rounded">
                                {scans.length}
                            </span>
                        </h2>
                    </div>

                    {scans.length === 0 && (
                        <div className="text-center py-16 px-4">
                            <Shield className="w-20 h-20 text-gray-600 mx-auto mb-4" />
                            <p className="text-gray-400 text-lg font-medium">No scans found</p>
                            <p className="text-sm text-gray-500 mt-2">
                                Developers can trigger scans from their dashboards
                            </p>
                        </div>
                    )}

                    {scans.length > 0 && (
                        <div className="overflow-x-auto">
                            <table className="table w-full">
                                <thead className="bg-[#05080C]">
                                    <tr className="border-b border-white/10">
                                        <th className="text-gray-400 font-semibold">Repository</th>
                                        <th className="text-gray-400 font-semibold">Status</th>
                                        <th className="text-gray-400 font-semibold hidden md:table-cell">Commit</th>
                                        <th className="text-gray-400 font-semibold hidden lg:table-cell">Started</th>
                                        <th className="text-gray-400 font-semibold text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {scans.map((scan) => {
                                        const config = getStatusConfig(scan.status);
                                        const Icon = config.icon;
                                        const isDeleting = deleting === scan.id;

                                        return (
                                            <tr key={scan.id} className="border-b border-white/10 hover:bg-white/5 transition-colors">
                                                <td>
                                                    <div className="flex flex-col">
                                                        <p className="font-semibold text-white">{scan.repository_name}</p>
                                                        <p className="text-xs text-gray-500">Scan #{scan.id}</p>
                                                    </div>
                                                </td>
                                                <td>
                                                    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded border text-sm font-medium ${config.className}`}>
                                                        <Icon className="w-4 h-4" />
                                                        <span className="hidden sm:inline">{config.text}</span>
                                                    </span>
                                                </td>
                                                <td className="hidden md:table-cell">
                                                    <span className="font-mono text-sm text-gray-400">
                                                        {scan.commit_hash ? scan.commit_hash.substring(0, 7) : 'N/A'}
                                                    </span>
                                                </td>
                                                <td className="text-sm text-gray-400 hidden lg:table-cell">
                                                    {new Date(scan.created_at).toLocaleString()}
                                                </td>
                                                <td>
                                                    <div className="flex items-center justify-end gap-2">
                                                        {scan.status === 'completed' && (
                                                            <button
                                                                onClick={() => navigate(`/tenant-dashboard/scans/${scan.id}`)}
                                                                className="btn btn-sm bg-primary/20 hover:bg-primary/30 text-primary border-none"
                                                            >
                                                                <span className="hidden sm:inline">View Results</span>
                                                                <span className="sm:hidden">View</span>
                                                            </button>
                                                        )}
                                                        {scan.status !== 'queued' && scan.status !== 'running' && (
                                                            <button
                                                                onClick={() => handleDeleteScan(scan)}
                                                                disabled={isDeleting}
                                                                className="btn btn-sm bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/20"
                                                                title="Delete scan"
                                                            >
                                                                {isDeleting ? (
                                                                    <span className="loading loading-spinner loading-xs"></span>
                                                                ) : (
                                                                    <Trash2 className="w-4 h-4" />
                                                                )}
                                                            </button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </>
    );
};

export default Scans;
