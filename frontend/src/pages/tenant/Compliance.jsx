import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Search, CheckCircle, XCircle, Loader2, RefreshCw, FileCheck2, Award, Trash2, Eye, X, Clock } from 'lucide-react';
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

const EvaluationDetailModal = ({ evaluation, onClose }) => {
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDetails = async () => {
            try {
                const response = await api.get(`/compliance/evaluations/${evaluation.id}/`);
                setDetails(response.data);
            } catch (error) {
                console.error('Failed to fetch evaluation details:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchDetails();
    }, [evaluation.id]);

    const scoreData = details?.score || {};
    const results = details?.rule_results || [];
    const score = parseFloat(scoreData.total_score) || parseFloat(evaluation.score) || 0;
    const grade = getScoreGrade(score);
    const passedRules = scoreData.passed_count ?? results.filter(r => r.passed).length;
    const failedRules = scoreData.failed_count ?? results.filter(r => !r.passed).length;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="bg-[#0A0F16] border border-white/10 rounded-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-white/10">
                    <div className="flex items-center gap-3">
                        <Award className={`w-8 h-8 ${getGradeColor(grade).split(' ')[0]}`} />
                        <div>
                            <h2 className="text-lg font-bold text-white">
                                Evaluation #{evaluation.id}
                            </h2>
                            <p className="text-sm text-gray-400">
                                {evaluation.repository_name} • {evaluation.standard_name}
                            </p>
                        </div>
                    </div>
                    <button onClick={onClose} className="btn btn-ghost btn-sm btn-circle">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Score Summary */}
                <div className="p-4 bg-[#05080C] border-b border-white/10">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className={`text-4xl font-bold px-4 py-2 rounded-lg border ${getGradeColor(grade)}`}>
                                {grade}
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-white">{score.toFixed(1)}%</p>
                                <p className="text-sm text-gray-400">Compliance Score</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="flex items-center gap-4 text-sm">
                                <span className="text-green-400">{passedRules} passed</span>
                                <span className="text-red-400">{failedRules} failed</span>
                            </div>
                            <div className="flex items-center gap-1 text-xs text-gray-500 mt-1">
                                <Clock className="w-3 h-3" />
                                {new Date(evaluation.completed_at || evaluation.created_at).toLocaleString()}
                            </div>
                            {details?.commit_hash && (
                                <div className="text-xs text-gray-600 mt-1 font-mono">
                                    {details.commit_hash.substring(0, 7)}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Rules List */}
                <div className="flex-1 overflow-y-auto p-4">
                    <h3 className="text-sm font-semibold text-gray-400 mb-3">Rule Results</h3>
                    {loading ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="w-6 h-6 animate-spin text-primary" />
                        </div>
                    ) : results.length === 0 ? (
                        <p className="text-gray-500 text-center py-8">No rule results available</p>
                    ) : (
                        <div className="space-y-2">
                            {results.map((result, index) => (
                                <div
                                    key={index}
                                    className={`flex items-start gap-3 p-3 rounded-lg border ${result.passed
                                        ? 'bg-green-500/5 border-green-500/20'
                                        : 'bg-red-500/5 border-red-500/20'
                                        }`}
                                >
                                    {result.passed ? (
                                        <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                                    ) : (
                                        <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                                    )}
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-white">
                                            {result.rule_name || `Rule #${result.rule}`}
                                        </p>
                                        {result.message && (
                                            <p className="text-xs text-gray-400 mt-1">{result.message}</p>
                                        )}
                                        {result.remediation_hint && !result.passed && (
                                            <p className="text-xs text-yellow-400 mt-1">💡 {result.remediation_hint}</p>
                                        )}
                                    </div>
                                    {result.severity && (
                                        <span className={`text-xs px-2 py-0.5 rounded ${result.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                                            result.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                                                result.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                                    'bg-gray-500/20 text-gray-400'
                                            }`}>
                                            {result.severity}
                                        </span>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-white/10">
                    <button onClick={onClose} className="btn btn-ghost w-full">
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

const EvaluationRow = ({ evaluation, onUpdate, onDelete, onView, isOwner }) => {
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
        const displayScore = parseFloat(score) || 0;
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
            <td>
                <div className="flex items-center gap-1">
                    {currentStatus === 'completed' && (
                        <button
                            onClick={() => onView(evaluation)}
                            className="btn btn-ghost btn-xs text-primary hover:text-primary/80"
                            title="View details"
                        >
                            <Eye className="w-4 h-4" />
                        </button>
                    )}
                    {isOwner && (
                        <button
                            onClick={() => onDelete(evaluation)}
                            className="btn btn-ghost btn-xs text-red-400 hover:text-red-300 hover:bg-red-500/10"
                            title="Delete evaluation"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    )}
                </div>
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
    const [selectedEvaluation, setSelectedEvaluation] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

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

    // Filter evaluations by search term
    const filteredEvaluations = evaluations.filter(e =>
        (e.repository_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (e.standard_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        String(e.id).includes(searchTerm)
    );

    return (
        <>
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight flex items-center gap-2">
                        <FileCheck2 className="w-8 h-8 text-primary" />
                        Evaluation Results
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

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                    type="text"
                    placeholder="Search by repository, standard, or ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-[#0A0F16] border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary/50"
                />
            </div>

            <div className="bg-[#0A0F16] rounded-xl border border-white/10 overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    </div>
                ) : filteredEvaluations.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        <Award className="w-12 h-12 mx-auto mb-4 text-gray-600" />
                        <p className="text-lg">{searchTerm ? 'No evaluations match your search' : 'No evaluations yet'}</p>
                        <p className="text-sm mt-2">
                            {searchTerm ? 'Try a different search term' : 'Assign standards to repositories and trigger evaluations to see compliance scores'}
                        </p>
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
                                    <th className="text-gray-400 font-semibold">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredEvaluations.map(evaluation => (
                                    <EvaluationRow
                                        key={evaluation.id}
                                        evaluation={evaluation}
                                        onUpdate={fetchEvaluations}
                                        onDelete={handleDeleteClick}
                                        onView={setSelectedEvaluation}
                                        isOwner={isOwner}
                                    />
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Detail Modal */}
            {selectedEvaluation && (
                <EvaluationDetailModal
                    evaluation={selectedEvaluation}
                    onClose={() => setSelectedEvaluation(null)}
                />
            )}

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
