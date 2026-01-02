import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { ExternalLink, Play, Shield, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';
// import useWebSocket from '../../hooks/useWebSocket'; // Removed useWebSocket

const ScanButton = ({ repo, tenantId, onScanComplete }) => {
    const [scanning, setScanning] = useState(false);
    const [scanId, setScanId] = useState(null);
    const [progress, setProgress] = useState(0);
    const [scanStatus, setScanStatus] = useState(null);
    const navigate = useNavigate(); // Added useNavigate

    // checking for running scans on mount
    useEffect(() => {
        const checkRunningScan = async () => {
            try {
                const response = await api.get(`/scans/repository/${repo.id}/`);
                const scans = response.data || [];
                const runningScan = scans.find(s => s.status === 'queued' || s.status === 'running');
                if (runningScan) {
                    setScanId(runningScan.id);
                    setScanStatus(runningScan.status);
                    setScanning(true);
                }
            } catch (err) {
                // no scans or error - ignore
            }
        };
        checkRunningScan();
    }, [repo.id]);

    // poll for scan status updates (since WebSocket isn't implemented yet)
    useEffect(() => {
        if (!scanId || !scanning) return;

        const pollInterval = setInterval(async () => {
            try {
                const response = await api.get(`/scans/${scanId}/`);
                const data = response.data;

                setScanStatus(data.status);

                if (data.status === 'completed') {
                    setScanning(false);
                    clearInterval(pollInterval);
                    onScanComplete?.(repo.id, 'completed', scanId);
                    toast.success(`Scan completed for ${repo.name}`);
                    // auto-navigate to results after 1 second
                    setTimeout(() => {
                        navigate(`/dev-dashboard/scans/${scanId}`);
                    }, 1000);
                } else if (data.status === 'failed') {
                    setScanning(false);
                    clearInterval(pollInterval);
                    onScanComplete?.(repo.id, 'failed', scanId);
                    toast.error(`Scan failed for ${repo.name}`);
                }
            } catch (error) {
                console.error('Error polling scan status:', error);
            }
        }, 3000); // Poll every 3 seconds

        return () => clearInterval(pollInterval);
    }, [scanId, scanning, repo.id, repo.name, navigate, onScanComplete]);

    const handleTriggerScan = async () => {
        try {
            setScanning(true);
            setProgress(0);
            setScanStatus('queued');

            const response = await api.post(`/scans/trigger/${repo.id}/`);

            // checking if this is an existing scan (200 OK) or new scan (201 Created)
            if (response.status === 200 && response.data.message) {
                // already scanned - show message and navigate to existing results
                setScanning(false);
                toast.info(response.data.message || 'Repository already scanned');
                const existingScanId = response.data.scan?.id;
                if (existingScanId) {
                    onScanComplete?.(repo.id, 'completed', existingScanId);
                    setTimeout(() => {
                        navigate(`/dev-dashboard/scans/${existingScanId}`);
                    }, 1000);
                }
                return;
            }

            // new scan created (201)
            const newScanId = response.data.id;
            setScanId(newScanId);
            toast.info(`Scan started for ${repo.name}`);
        } catch (error) {
            setScanning(false);
            setScanStatus(null);
            toast.error(error.response?.data?.error || 'Failed to trigger scan');
        }
    };

    if (scanning) {
        return (
            <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                    <span className="text-sm text-blue-400">
                        {scanStatus === 'queued' && 'Queued...'}
                        {scanStatus === 'running' && `${progress}%`}
                    </span>
                </div>
                {progress > 0 && (
                    <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-blue-500 transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                )}
            </div>
        );
    }

    return (
        <button
            className="btn btn-sm bg-primary hover:bg-primary/80 border-none text-white"
            onClick={handleTriggerScan}
        >
            <Play className="w-4 h-4 mr-1" />
            Scan
        </button>
    );
};

const Repositories = () => {
    const { tenant } = useAuth();
    const navigate = useNavigate();
    const [repos, setRepos] = useState([]);
    const [loading, setLoading] = useState(false);
    const [lastScanResults, setLastScanResults] = useState({});

    useEffect(() => {
        const fetchRepos = async () => {
            if (!tenant) return;
            setLoading(true);
            try {
                const response = await api.get(`/tenants/${tenant.id}/repositories/`);
                const repositories = response.data.repositories || [];
                setRepos(repositories.map(r => ({
                    ...r,
                    orgName: tenant.name,
                    orgId: tenant.id
                })));
            } catch (error) {
                toast.error('Failed to load repositories');
                setRepos([]);
            } finally {
                setLoading(false);
            }
        };
        fetchRepos();
    }, [tenant]);

    const handleScanComplete = (repoId, status, scanId) => {
        setLastScanResults(prev => ({
            ...prev,
            [repoId]: { status, timestamp: new Date(), scanId }
        }));
    };

    const getLastScanBadge = (repoId) => {
        const result = lastScanResults[repoId];
        if (!result) return null;

        if (result.status === 'completed') {
            return (
                <button
                    onClick={() => result.scanId && navigate(`/dev-dashboard/scans/${result.scanId}`)}
                    className="flex items-center gap-1 px-2 py-0.5 bg-green-500/10 text-green-400 border border-green-500/20 rounded text-xs hover:bg-green-500/20 transition-colors"
                >
                    <CheckCircle className="w-3 h-3" />
                    View Results
                </button>
            );
        }
        if (result.status === 'failed') {
            return (
                <span className="flex items-center gap-1 px-2 py-0.5 bg-red-500/10 text-red-400 border border-red-500/20 rounded text-xs">
                    <XCircle className="w-3 h-3" />
                    Failed
                </span>
            );
        }
        return null;
    };

    return (
        <>
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">Repositories</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        View your assigned repositories and trigger security scans.
                    </p>
                </div>
            </div>

            {loading && (
                <div className="flex items-center justify-center py-12">
                    <span className="loading loading-spinner loading-lg text-primary"></span>
                </div>
            )}

            {!loading && (
                <div className="bg-[#0A0F16] shadow-xl rounded-xl border border-white/10 p-6">
                    <h2 className="text-xl font-bold mb-4 flex items-center text-white">
                        <ExternalLink className="w-5 h-5 mr-2" /> Assigned Repositories ({repos.length})
                    </h2>
                    <div className="space-y-4">
                        {repos.map(repo => (
                            <div key={repo.id} className="flex flex-col md:flex-row items-center justify-between p-4 bg-[#05080C] border border-white/10 rounded-lg gap-4">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                        <h3 className="font-bold text-lg text-white">{repo.name}</h3>
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${repo.visibility === 'private' ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'
                                            }`}>
                                            {repo.visibility}
                                        </span>
                                        {getLastScanBadge(repo.id)}
                                    </div>
                                    <p className="text-xs text-gray-500 mb-1">Organization: {repo.orgName}</p>
                                    {repo.description && (
                                        <p className="text-sm text-gray-400 mb-2">{repo.description}</p>
                                    )}
                                    <div className="flex items-center gap-4 mb-2">
                                        {repo.primary_language && (
                                            <span className="text-xs text-blue-400">{repo.primary_language}</span>
                                        )}
                                        {repo.stars_count > 0 && (
                                            <span className="text-xs text-yellow-400">Stars: {repo.stars_count}</span>
                                        )}
                                        {repo.forks_count > 0 && (
                                            <span className="text-xs text-gray-400">Forks: {repo.forks_count}</span>
                                        )}
                                    </div>
                                    <a href={repo.url} target="_blank" rel="noreferrer" className="text-sm hover:underline flex items-center text-blue-400">
                                        {repo.url} <ExternalLink className="w-3 h-3 ml-1" />
                                    </a>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="text-right">
                                        <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${repo.validation_status === 'valid' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                            repo.validation_status === 'invalid' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                                repo.validation_status === 'access_denied' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                                                    'bg-gray-500/10 text-gray-400 border-gray-500/20'
                                            }`}>
                                            {repo.validation_status ? repo.validation_status.replace('_', ' ').toUpperCase() : 'Pending'}
                                        </span>
                                        <div className="text-xs text-gray-500 mt-1">
                                            Added {new Date(repo.created_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                    <ScanButton
                                        repo={repo}
                                        tenantId={tenant?.id}
                                        onScanComplete={handleScanComplete}
                                    />
                                </div>
                            </div>
                        ))}
                        {repos.length === 0 && (
                            <div className="flex flex-col items-center gap-3 py-12">
                                <Shield className="w-16 h-16 text-gray-600" />
                                <p className="text-gray-400 text-lg">No repositories assigned to you</p>
                                <p className="text-sm text-gray-500">
                                    Contact your tenant owner to get repository access
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </>
    );
};

export default Repositories;
