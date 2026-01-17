import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { ExternalLink, Play, Shield, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';
import useScanWebSocket from '../../hooks/useScanWebSocket';

const ScanButton = ({ repo, tenantId, onScanComplete }) => {
    const navigate = useNavigate();

    // 1. Helper to safely read cache
    const getCache = () => {
        try {
            const key = `running_scan_${repo.id}`;
            const cached = localStorage.getItem(key);
            console.debug(`[ScanDebug:${repo.id}] Reading cache key=${key}:`, cached);
            return cached ? JSON.parse(cached) : null;
        } catch (e) {
            console.error(`[ScanDebug:${repo.id}] Cache read error:`, e);
            return null;
        }
    };

    // 2. Initialize state atomically from cache (Lazy Init)
    const [state, setState] = useState(() => {
        const cache = getCache();
        const hasCache = !!cache;

        console.debug(`[ScanDebug:${repo.id}] Mount. HasCache=${hasCache}`, cache);

        return {
            scanning: hasCache,
            scanId: cache?.id || null,
            // Default to 'queued' to prevent "Connecting..." flicker if status is missing
            initialStatus: cache?.status || 'queued',
            initialProgress: cache?.progress || 0,
            initialMessage: cache?.message || 'Initializing scan...',
            // If cache exists, we KNOW we are scanning, so no checking needed.
            // If cache missing, we MUST check.
            checkingStatus: !hasCache
        };
    });

    const { scanning, scanId, initialStatus, initialProgress, initialMessage, checkingStatus } = state;

    // Helper to merge state updates and log them
    const updateState = (updates) => {
        console.debug(`[ScanDebug:${repo.id}] UpdateState:`, updates);
        setState(prev => ({ ...prev, ...updates }));
    };

    const { status: wsStatus, progress: wsProgress, message: wsMessage, isConnected } = useScanWebSocket(scanId);

    // 3. Persist state to localStorage on any change
    useEffect(() => {
        const key = `running_scan_${repo.id}`;
        if (scanning && scanId) {
            const data = {
                id: scanId,
                status: wsStatus || initialStatus,
                progress: wsProgress ?? initialProgress,
                message: wsMessage || initialMessage
            };
            // Only log if data actually changed to avoid spam
            // console.debug(`[ScanDebug:${repo.id}] Saving cache:`, data);
            localStorage.setItem(key, JSON.stringify(data));
        } else if (!scanning) {
            // Only log if we are clearing an existing cache
            if (localStorage.getItem(key)) {
                console.debug(`[ScanDebug:${repo.id}] Clearing cache (Scanning=false)`);
                localStorage.removeItem(key);
            }
        }
    }, [scanning, scanId, wsStatus, wsProgress, wsMessage, initialStatus, initialProgress, initialMessage, repo.id]);

    // 4. Check API for running scans on mount (Truth Source)
    useEffect(() => {
        const checkRunningScan = async () => {
            if (scanning) return; // If cache says running, trust it first, background update later? No, check anyway to confirm.

            console.debug(`[ScanDebug:${repo.id}] Checking API for running scan...`);
            try {
                const response = await api.get(`/scans/repository/${repo.id}/`);
                const scans = response.data || [];
                const runningScan = scans.find(s => s.status === 'queued' || s.status === 'running');

                if (runningScan) {
                    console.debug(`[ScanDebug:${repo.id}] API found running scan:`, runningScan.id);
                    updateState({
                        scanId: runningScan.id,
                        scanning: true,
                        initialStatus: runningScan.status,
                        initialProgress: runningScan.progress || 0,
                        initialMessage: runningScan.progress_message || 'Resuming scan...',
                        checkingStatus: false
                    });
                } else {
                    console.debug(`[ScanDebug:${repo.id}] API returned no running scans.`);
                    // Only turn off if we were checking. If we were already scanning (from cache) and API says no, 
                    // it means scan finished or failed remotely.
                    updateState({ scanning: false, checkingStatus: false });
                    localStorage.removeItem(`running_scan_${repo.id}`);
                }
            } catch (err) {
                console.error(`[ScanDebug:${repo.id}] API Check Failed:`, err);
                updateState({ checkingStatus: false });
            }
        };
        checkRunningScan();
    }, [repo.id]); // Run only on mount/repo change


    // 5. Handle WebSocket updates
    useEffect(() => {
        if (!wsStatus || !scanId) return;

        if (wsStatus === 'completed') {
            console.debug(`[ScanDebug:${repo.id}] WebSocket Completed`);
            updateState({ scanning: false });
            onScanComplete?.(repo.id, 'completed', scanId);
            toast.success(`Scan completed for ${repo.name}`);
            navigate(`/dev-dashboard/scans/${scanId}`);
        } else if (wsStatus === 'failed') {
            console.debug(`[ScanDebug:${repo.id}] WebSocket Failed`);
            updateState({ scanning: false });
            onScanComplete?.(repo.id, 'failed', scanId);
            toast.error(`Scan failed for ${repo.name}`);
        }
    }, [wsStatus, scanId]);

    const handleTriggerScan = async () => {
        try {
            console.debug(`[ScanDebug:${repo.id}] Triggering Scan...`);
            // Optimistic update
            updateState({
                scanning: true,
                checkingStatus: false,
                initialStatus: 'queued',
                initialMessage: 'Requesting scan...'
            });

            const response = await api.post(`/scans/trigger/${repo.id}/`);

            if (response.status === 200 && response.data.message) {
                console.debug(`[ScanDebug:${repo.id}] Trigger Info:`, response.data.message);
                updateState({ scanning: false });
                toast.info(response.data.message || 'Repository already scanned');
                const existingScanId = response.data.scan?.id;
                if (existingScanId) {
                    onScanComplete?.(repo.id, 'completed', existingScanId);
                    navigate(`/dev-dashboard/scans/${existingScanId}`);
                }
                return;
            }

            const newScanId = response.data.id;
            console.debug(`[ScanDebug:${repo.id}] Scan Started ID:`, newScanId);
            updateState({ scanId: newScanId });
            toast.info(`Scan started for ${repo.name}`);
        } catch (error) {
            console.error(`[ScanDebug:${repo.id}] Trigger Failed:`, error);
            updateState({ scanning: false });
            toast.error(error.response?.data?.error || 'Failed to trigger scan');
        }
    };

    const displayStatus = wsStatus || initialStatus || 'queued';
    const displayProgress = wsProgress ?? initialProgress;
    const displayMessage = wsMessage || initialMessage ||
        (displayStatus === 'queued' ? 'Waiting in queue...' :
            displayStatus === 'running' ? 'Scanning in progress...' : 'Connecting...');

    if (scanning) {
        return (
            <div className="flex flex-col gap-2 min-w-[180px]">
                <div className="flex items-center gap-2 px-3 py-2 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                        <p className="text-xs text-blue-300 truncate" title={displayMessage}>
                            {displayMessage}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                            <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-500 ease-out"
                                    style={{ width: `${displayProgress}%` }}
                                />
                            </div>
                            <span className="text-xs font-medium text-blue-400 w-8 text-right">
                                {displayProgress}%
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // show loading indicator while checking for running scan (Initial Cache Miss)
    if (checkingStatus) {
        return (
            <div className="btn btn-sm btn-ghost loading loading-spinner loading-sm text-gray-500" title="Checking status..."></div>
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
    const [lastScanTimes, setLastScanTimes] = useState({});

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

                repositories.forEach(async (repo) => {
                    try {
                        const scanResponse = await api.get(`/scans/repository/${repo.id}/`);
                        const scans = scanResponse.data || [];
                        const lastScan = scans.find(s => s.status === 'completed');
                        if (lastScan) {
                            setLastScanTimes(prev => ({
                                ...prev,
                                [repo.id]: lastScan.completed_at
                            }));
                        }
                    } catch (err) {
                    }
                });
            } catch (error) {
                toast.error('Failed to load repositories');
                setRepos([]);
            } finally {
                setLoading(false);
            }
        };
        fetchRepos();
    }, [tenant]);

    const handleScanComplete = useCallback((repoId, status, scanId) => {
        setLastScanResults(prev => ({
            ...prev,
            [repoId]: { status, timestamp: new Date(), scanId }
        }));
        if (status === 'completed') {
            setLastScanTimes(prev => ({
                ...prev,
                [repoId]: new Date().toISOString()
            }));
        }
    }, []);

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
                                        {lastScanTimes[repo.id] ? (
                                            <>
                                                <span className="px-2 py-0.5 rounded text-xs font-semibold border bg-blue-500/10 text-blue-400 border-blue-500/20">
                                                    Last Scanned
                                                </span>
                                                <div className="text-xs text-gray-400 mt-1">
                                                    {new Date(lastScanTimes[repo.id]).toLocaleString()}
                                                </div>
                                            </>
                                        ) : (
                                            <>
                                                <span className="px-2 py-0.5 rounded text-xs font-semibold border bg-gray-500/10 text-gray-400 border-gray-500/20">
                                                    Never Scanned
                                                </span>
                                                <div className="text-xs text-gray-500 mt-1">
                                                    Added {new Date(repo.created_at).toLocaleDateString()}
                                                </div>
                                            </>
                                        )}
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
