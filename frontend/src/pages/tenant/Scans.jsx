import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Search, Clock, CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';
import useWebSocket from '../../hooks/useWebSocket';

const ScanRow = ({ scan, onUpdate }) => {
    const [currentStatus, setCurrentStatus] = useState(scan.status);
    const [progress, setProgress] = useState(scan.progress || 0);

    const shouldConnect = currentStatus === 'queued' || currentStatus === 'running';

    useWebSocket(shouldConnect ? scan.id : null, {
        onMessage: (data) => {
            if (data.status) setCurrentStatus(data.status);
            if (data.progress !== undefined) setProgress(data.progress);
            if (data.status === 'completed' || data.status === 'failed') {
                onUpdate?.();
            }
        }
    });

    const getStatusBadge = () => {
        switch (currentStatus) {
            case 'completed':
                return (
                    <span className="flex items-center gap-1 px-2 py-1 bg-green-500/10 text-green-400 border border-green-500/20 rounded text-xs">
                        <CheckCircle className="w-3 h-3" /> Completed
                    </span>
                );
            case 'failed':
                return (
                    <span className="flex items-center gap-1 px-2 py-1 bg-red-500/10 text-red-400 border border-red-500/20 rounded text-xs">
                        <XCircle className="w-3 h-3" /> Failed
                    </span>
                );
            case 'running':
                return (
                    <span className="flex items-center gap-1 px-2 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded text-xs">
                        <Loader2 className="w-3 h-3 animate-spin" /> Running {progress}%
                    </span>
                );
            case 'queued':
                return (
                    <span className="flex items-center gap-1 px-2 py-1 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 rounded text-xs">
                        <Clock className="w-3 h-3" /> Queued
                    </span>
                );
            default:
                return (
                    <span className="px-2 py-1 bg-gray-500/10 text-gray-400 border border-gray-500/20 rounded text-xs">
                        {currentStatus}
                    </span>
                );
        }
    };

    return (
        <tr className="border-b border-white/5 hover:bg-white/5">
            <td className="text-white font-medium">{scan.id}</td>
            <td className="text-gray-300">{scan.repository_name || `Repo #${scan.repository}`}</td>
            <td>{getStatusBadge()}</td>
            <td className="text-gray-400 text-sm">
                {scan.started_at ? new Date(scan.started_at).toLocaleString() : '-'}
            </td>
            <td className="text-gray-400 text-sm">
                {scan.completed_at ? new Date(scan.completed_at).toLocaleString() : '-'}
            </td>
            <td className="text-gray-400 text-sm">{scan.findings_count || 0}</td>
        </tr>
    );
};

const Scans = () => {
    const { tenant } = useAuth();
    const [scans, setScans] = useState([]);
    const [loading, setLoading] = useState(false);
    const [repositories, setRepositories] = useState([]);

    const fetchScans = async () => {
        if (!tenant) return;
        setLoading(true);
        try {
            const reposRes = await api.get(`/tenants/${tenant.id}/repositories/`);
            const repos = reposRes.data.repositories || [];
            setRepositories(repos);

            const allScans = [];
            for (const repo of repos) {
                try {
                    const scansRes = await api.get(`/repos/${repo.id}/scans/`);
                    const repoScans = (scansRes.data || []).map(s => ({
                        ...s,
                        repository_name: repo.name
                    }));
                    allScans.push(...repoScans);
                } catch (err) {
                    // Skip repos with no scans
                }
            }
            allScans.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            setScans(allScans);
        } catch (error) {
            toast.error('Failed to load scans');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchScans();
    }, [tenant]);

    return (
        <>
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">Scans</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        View and manage security scans across all repositories.
                    </p>
                </div>
                <button
                    onClick={fetchScans}
                    className="btn btn-sm bg-white/5 border-white/10 text-gray-300 hover:bg-white/10"
                    disabled={loading}
                >
                    <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                </button>
            </div>

            <div className="bg-[#0A0F16] rounded-xl border border-white/10 overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    </div>
                ) : scans.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        <Search className="w-12 h-12 mx-auto mb-4 text-gray-600" />
                        <p className="text-lg">No scans yet</p>
                        <p className="text-sm mt-2">Trigger a scan from the Repositories page</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="table w-full">
                            <thead>
                                <tr className="border-b border-white/10">
                                    <th className="text-gray-400 font-semibold">ID</th>
                                    <th className="text-gray-400 font-semibold">Repository</th>
                                    <th className="text-gray-400 font-semibold">Status</th>
                                    <th className="text-gray-400 font-semibold">Started</th>
                                    <th className="text-gray-400 font-semibold">Completed</th>
                                    <th className="text-gray-400 font-semibold">Findings</th>
                                </tr>
                            </thead>
                            <tbody>
                                {scans.map(scan => (
                                    <ScanRow 
                                        key={scan.id} 
                                        scan={scan} 
                                        onUpdate={fetchScans}
                                    />
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </>
    );
};

export default Scans;
