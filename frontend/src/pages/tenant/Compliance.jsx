import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Search, CheckCircle, XCircle, Loader2, RefreshCw, TrendingUp, TrendingDown, Minus, Shield, Award, Trash2 } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';
import { deleteEvaluation } from '../../api/services/compliance';
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

const EvaluationRow = ({ evaluation, onUpdate, onDelete, isOwner }) => {
    const [currentStatus, setCurrentStatus] = useState(evaluation.status);
    const [progress, setProgress] = useState(evaluation.progress || 0);
    const [score, setScore] = useState(evaluation.score);

    const shouldConnect = currentStatus === 'pending' || currentStatus === 'running';

    useWebSocket(shouldConnect ? evaluation.id : null, {
        onMessage: (data) => {
            if (data.status) setCurrentStatus(data.status);
            if (data.progress !== undefined) setProgress(data.progress);
            if (data.score !== undefined) setScore(data.score);
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
            case 'pending':
                return (
                    <span className="flex items-center gap-1 px-2 py-1 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 rounded text-xs">
                        <Loader2 className="w-3 h-3" /> Pending
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

    const getScoreBadge = () => {
        if (!score && currentStatus !== 'completed') return '-';
        const displayScore = score || 0;
        const grade = getScoreGrade(displayScore);
        return (
            <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded text-xs font-bold border ${getGradeColor(grade)}`}>
                    {grade}
                </span>
                <span className="text-white font-medium">{displayScore.toFixed(1)}%</span>
            </div>
        );
    };

    const getTrendIcon = () => {
        if (!evaluation.score_change) return null;
        const change = evaluation.score_change;
        if (change > 0) return <TrendingUp className="w-4 h-4 text-green-400" />;
        if (change < 0) return <TrendingDown className="w-4 h-4 text-red-400" />;
        return <Minus className="w-4 h-4 text-gray-400" />;
    };

    return (
        <tr className="border-b border-white/5 hover:bg-white/5">
            <td className="text-white font-medium">#{evaluation.id}</td>
            <td className="text-gray-300">{evaluation.repository_name || `Repo #${evaluation.repository}`}</td>
            <td className="text-blue-400">{evaluation.standard_name || `Standard #${evaluation.standard}`}</td>
            <td>{getScoreBadge()}</td>
            <td>{getStatusBadge()}</td>
            <td className="text-gray-400 text-sm">
                {evaluation.completed_at
                    ? new Date(evaluation.completed_at).toLocaleString()
                    : evaluation.created_at
                        ? new Date(evaluation.created_at).toLocaleString()
                        : '-'}
            </td>
            <td className="text-gray-400 text-sm flex items-center gap-1">
                {evaluation.passed_count !== undefined && (
                    <>
                        <span className="text-green-400">{evaluation.passed_count}</span>/
                        <span className="text-gray-400">{evaluation.total_rules || (evaluation.passed_count + evaluation.failed_count)}</span>
                        {getTrendIcon()}
                    </>
                )}
            </td>
            <td>
                {isOwner && (
                    <button
                        onClick={() => onDelete(evaluation)}
                        className="btn btn-ghost btn-xs text-red-400 hover:text-red-300 hover:bg-red-500/10"
                        title="Delete evaluation"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                )}
            </td>
        </tr>
    );
};

const Compliance = () => {
    const { tenant, user } = useAuth();
    const [evaluations, setEvaluations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [repositories, setRepositories] = useState([]);
    const [deleteConfirm, setDeleteConfirm] = useState(null);
    const [deleting, setDeleting] = useState(false);

    // Check if current user is tenant owner
    const isOwner = tenant?.role === 'owner' || user?.is_staff;

    const fetchEvaluations = async () => {
        if (!tenant) return;
        setLoading(true);
        try {
            const reposRes = await api.get(`/tenants/${tenant.id}/repositories/`);
            const repos = reposRes.data.repositories || [];
            setRepositories(repos);

            const allEvaluations = [];
            for (const repo of repos) {
                try {
                    const evalRes = await api.get(`/compliance/repositories/${repo.id}/evaluations/`);
                    const repoEvals = (evalRes.data || []).map(e => ({
                        ...e,
                        repository_name: repo.name
                    }));
                    allEvaluations.push(...repoEvals);
                } catch (err) {
                    // Skip repos with no evaluations
                }
            }
            allEvaluations.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            setEvaluations(allEvaluations);
        } catch (error) {
            toast.error('Failed to load evaluations');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchEvaluations();
    }, [tenant]);

    const handleDeleteClick = (evaluation) => {
        setDeleteConfirm(evaluation);
    };

    const handleDeleteConfirm = async () => {
        if (!deleteConfirm) return;
        setDeleting(true);
        try {
            await deleteEvaluation(deleteConfirm.id);
            toast.success(`Evaluation #${deleteConfirm.id} deleted`);
            setDeleteConfirm(null);
            fetchEvaluations();
        } catch (error) {
            const msg = error.response?.data?.error || 'Failed to delete evaluation';
            toast.error(msg);
        } finally {
            setDeleting(false);
        }
    };

    return (
        <>
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight flex items-center gap-2">
                        <Shield className="w-8 h-8 text-primary" />
                        Compliance
                    </p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        View compliance evaluations and scores across all repositories.
                    </p>
                </div>
                <button
                    onClick={fetchEvaluations}
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
                ) : evaluations.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        <Award className="w-12 h-12 mx-auto mb-4 text-gray-600" />
                        <p className="text-lg">No evaluations yet</p>
                        <p className="text-sm mt-2">Assign standards to repositories and trigger evaluations to see compliance scores</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="table w-full">
                            <thead>
                                <tr className="border-b border-white/10">
                                    <th className="text-gray-400 font-semibold">ID</th>
                                    <th className="text-gray-400 font-semibold">Repository</th>
                                    <th className="text-gray-400 font-semibold">Standard</th>
                                    <th className="text-gray-400 font-semibold">Score</th>
                                    <th className="text-gray-400 font-semibold">Status</th>
                                    <th className="text-gray-400 font-semibold">Evaluated</th>
                                    <th className="text-gray-400 font-semibold">Rules</th>
                                    {isOwner && <th className="text-gray-400 font-semibold">Actions</th>}
                                </tr>
                            </thead>
                            <tbody>
                                {evaluations.map(evaluation => (
                                    <EvaluationRow
                                        key={evaluation.id}
                                        evaluation={evaluation}
                                        onUpdate={fetchEvaluations}
                                        onDelete={handleDeleteClick}
                                        isOwner={isOwner}
                                    />
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Delete Confirmation Modal */}
            {deleteConfirm && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-[#0A0F16] border border-white/10 rounded-xl p-6 max-w-md w-full mx-4">
                        <h3 className="text-lg font-bold text-white mb-2">Delete Evaluation</h3>
                        <p className="text-gray-400 mb-4">
                            Are you sure you want to delete evaluation <span className="text-white font-medium">#{deleteConfirm.id}</span>
                            {deleteConfirm.repository_name && ` for ${deleteConfirm.repository_name}`}?
                        </p>
                        <p className="text-red-400 text-sm mb-4">
                            This will permanently delete all associated results and scores.
                        </p>
                        <div className="flex justify-end gap-3">
                            <button
                                className="btn btn-sm bg-white/5 border-white/10 text-gray-300 hover:bg-white/10"
                                onClick={() => setDeleteConfirm(null)}
                                disabled={deleting}
                            >
                                Cancel
                            </button>
                            <button
                                className="btn btn-sm bg-red-500 hover:bg-red-600 border-none text-white"
                                onClick={handleDeleteConfirm}
                                disabled={deleting}
                            >
                                {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4 mr-1" />}
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default Compliance;
