import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { ExternalLink, Play, Shield, Loader2, CheckCircle, XCircle, Award, Settings } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';
import useWebSocket from '../../hooks/useWebSocket';

const getGradeColor = (grade) => {
    switch (grade) {
        case 'A': return 'text-green-400 bg-green-500/10 border-green-500/20';
        case 'B': return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
        case 'C': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
        case 'D': return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
        case 'F': return 'text-red-400 bg-red-500/10 border-red-500/20';
        default: return 'text-gray-400 bg-gray-500/10 border-gray-500/20';
    }
};

const getScoreGrade = (score) => {
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
};

const EvaluateButton = ({ repo, tenantId, onEvaluationComplete }) => {
    const [evaluating, setEvaluating] = useState(false);
    const [evaluationId, setEvaluationId] = useState(null);
    const [progress, setProgress] = useState(0);
    const [evalStatus, setEvalStatus] = useState(null);
    const [latestScore, setLatestScore] = useState(null);

    // Check for running evaluations and get latest score on mount
    useEffect(() => {
        const checkRunningEvaluation = async () => {
            try {
                const response = await api.get(`/compliance/repositories/${repo.id}/evaluations/`);
                const evals = response.data || [];
                const runningEval = evals.find(e => e.status === 'pending' || e.status === 'running');
                if (runningEval) {
                    setEvaluationId(runningEval.id);
                    setEvalStatus(runningEval.status);
                    setEvaluating(true);
                }
                // Get latest completed evaluation
                const completed = evals.find(e => e.status === 'completed');
                if (completed?.score) {
                    setLatestScore(completed.score);
                }
            } catch (err) {
                // No evaluations or error - ignore
            }
        };
        checkRunningEvaluation();
    }, [repo.id]);

    useWebSocket(evaluationId, {
        onMessage: (data) => {
            if (data.status) {
                setEvalStatus(data.status);
            }
            if (data.progress !== undefined) {
                setProgress(data.progress);
            }
            if (data.status === 'completed' || data.status === 'failed') {
                setEvaluating(false);
                setEvaluationId(null);
                if (data.score) setLatestScore(data.score);
                onEvaluationComplete?.(repo.id, data.status, data.score);
                if (data.status === 'completed') {
                    toast.success(`Evaluation completed for ${repo.name}: ${data.score?.toFixed(1)}%`);
                } else {
                    toast.error(`Evaluation failed for ${repo.name}`);
                }
            }
        }
    });

    const handleTriggerEvaluation = async () => {
        try {
            // First, get assigned standards for this repo
            const standardsRes = await api.get(`/standards/repositories/${repo.id}/`);
            const assignedStandards = standardsRes.data || [];

            if (assignedStandards.length === 0) {
                toast.warning(`No standards assigned to ${repo.name}. Ask an owner to assign a standard.`);
                return;
            }

            // Use the first assigned standard
            const standardId = assignedStandards[0].standard;

            setEvaluating(true);
            setProgress(0);
            setEvalStatus('pending');

            const response = await api.post('/compliance/evaluations/trigger/', {
                repository_id: repo.id,
                standard_id: standardId
            });

            // Handle already evaluated response
            if (response.data.already_evaluated) {
                setEvaluating(false);
                setEvalStatus(null);
                if (response.data.score) {
                    setLatestScore(response.data.score);
                }
                toast.info(`Already evaluated at current commit (${response.data.score?.toFixed(0)}%). No changes detected.`);
                return;
            }

            const newEvalId = response.data.id;
            setEvaluationId(newEvalId);
            toast.info(`Evaluation started for ${repo.name}`);
        } catch (error) {
            setEvaluating(false);
            setEvalStatus(null);
            const errorMsg = error.response?.data?.error || 'Failed to trigger evaluation';
            toast.error(errorMsg);
        }
    };

    if (evaluating) {
        return (
            <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                    <span className="text-sm text-blue-400">
                        {evalStatus === 'pending' && 'Queued...'}
                        {evalStatus === 'running' && `${progress}%`}
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
        <div className="flex items-center gap-2">
            {latestScore !== null && (
                <span className={`px-2 py-1 rounded text-xs font-bold border ${getGradeColor(getScoreGrade(latestScore))}`}>
                    {getScoreGrade(latestScore)} {latestScore.toFixed(0)}%
                </span>
            )}
            <button
                className="btn btn-sm bg-primary hover:bg-primary/80 border-none text-white"
                onClick={handleTriggerEvaluation}
            >
                <Shield className="w-4 h-4 mr-1" />
                Evaluate
            </button>
        </div>
    );
};

const Repositories = () => {
    const { tenant } = useAuth();
    const [repos, setRepos] = useState([]);
    const [loading, setLoading] = useState(false);
    const [lastEvalResults, setLastEvalResults] = useState({});

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

    const handleEvaluationComplete = (repoId, status, score) => {
        setLastEvalResults(prev => ({
            ...prev,
            [repoId]: { status, score, timestamp: new Date() }
        }));
    };

    const getLastEvalBadge = (repoId) => {
        const result = lastEvalResults[repoId];
        if (!result) return null;

        if (result.status === 'completed') {
            const grade = getScoreGrade(result.score || 0);
            return (
                <span className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs border ${getGradeColor(grade)}`}>
                    <Award className="w-3 h-3" />
                    {grade} - {(result.score || 0).toFixed(0)}%
                </span>
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
                        View your assigned repositories and run compliance evaluations.
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
                                        {getLastEvalBadge(repo.id)}
                                    </div>
                                    <p className="text-xs text-gray-500 mb-1">Organization: {repo.orgName}</p>
                                    {repo.description && (
                                        <p className="text-sm text-gray-400 mb-2">{repo.description}</p>
                                    )}
                                    <div className="flex items-center gap-4 mb-2">
                                        {repo.primary_language && (
                                            <span className="text-xs text-blue-400">📝 {repo.primary_language}</span>
                                        )}
                                        {repo.stars_count > 0 && (
                                            <span className="text-xs text-yellow-400">⭐ {repo.stars_count}</span>
                                        )}
                                        {repo.forks_count > 0 && (
                                            <span className="text-xs text-gray-400">🍴 {repo.forks_count}</span>
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
                                    <EvaluateButton
                                        repo={repo}
                                        tenantId={tenant?.id}
                                        onEvaluationComplete={handleEvaluationComplete}
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
