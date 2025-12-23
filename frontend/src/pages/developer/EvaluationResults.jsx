import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { ClipboardCheck, Search, CheckCircle, XCircle, Loader2, RefreshCw, Eye, X, Award, Clock } from 'lucide-react';
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

const EvaluationRow = ({ evaluation, onClick }) => {
    const [currentStatus, setCurrentStatus] = useState(evaluation.status);
    const [progress, setProgress] = useState(evaluation.progress || 0);
    const [score, setScore] = useState(evaluation.score);

    const shouldConnect = currentStatus === 'pending' || currentStatus === 'running';

    useWebSocket(shouldConnect ? evaluation.id : null, {
        onMessage: (data) => {
            if (data.status) setCurrentStatus(data.status);
            if (data.progress !== undefined) setProgress(data.progress);
            if (data.score !== undefined) setScore(data.score);
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
        if (!score && currentStatus !== 'completed') return <span className="text-gray-500">-</span>;
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

    return (
        <tr
            className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
            onClick={() => currentStatus === 'completed' && onClick(evaluation)}
        >
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
                {currentStatus === 'completed' && (
                    <button
                        onClick={(e) => { e.stopPropagation(); onClick(evaluation); }}
                        className="btn btn-ghost btn-xs text-primary hover:text-primary/80"
                        title="View details"
                    >
                        <Eye className="w-4 h-4" />
                    </button>
                )}
            </td>
        </tr>
    );
};

const EvaluationDetailModal = ({ evaluation, onClose }) => {
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDetails = async () => {
            try {
                // Fetch full evaluation details including rule_results
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
                                        <span className={`text-xs px-2 py-0.5 rounded flex-shrink-0 ${result.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
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

const EvaluationResults = () => {
    const { tenant } = useAuth();
    const [evaluations, setEvaluations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedEvaluation, setSelectedEvaluation] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchEvaluations = async () => {
        if (!tenant) return;
        setLoading(true);
        try {
            // Get all repositories first
            const repoRes = await api.get(`/tenants/${tenant.id}/repositories/`);
            const repositories = repoRes.data.repositories || [];

            // Fetch evaluations for each repository
            const allEvaluations = [];
            for (const repo of repositories) {
                try {
                    const evalRes = await api.get(`/compliance/repositories/${repo.id}/evaluations/`);
                    const repoEvals = (evalRes.data || []).map(e => ({
                        ...e,
                        repository_name: repo.name
                    }));
                    allEvaluations.push(...repoEvals);
                } catch {
                    // Ignore errors for individual repos
                }
            }

            // Sort by created_at descending
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

    const filteredEvaluations = evaluations.filter(e =>
        (e.repository_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (e.standard_name || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <>
            {/* Header */}
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight flex items-center gap-2">
                        <ClipboardCheck className="w-7 h-7" />
                        Evaluation Results
                    </p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        View all compliance evaluation results for your repositories.
                    </p>
                </div>
                <button
                    onClick={fetchEvaluations}
                    disabled={loading}
                    className="btn btn-ghost btn-sm gap-2"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                </button>
            </div>

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                    type="text"
                    placeholder="Search by repository or standard..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-[#0A0F16] border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary/50"
                />
            </div>

            {/* Table */}
            <div className="bg-[#0A0F16] rounded-xl border border-white/10 overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    </div>
                ) : filteredEvaluations.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-16 text-gray-500">
                        <ClipboardCheck className="w-12 h-12 mb-4 opacity-50" />
                        <p className="text-lg font-medium">No evaluations yet</p>
                        <p className="text-sm">Run an evaluation from the Repositories page</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="table w-full">
                            <thead>
                                <tr className="border-b border-white/10">
                                    <th className="text-gray-400 font-medium">ID</th>
                                    <th className="text-gray-400 font-medium">Repository</th>
                                    <th className="text-gray-400 font-medium">Standard</th>
                                    <th className="text-gray-400 font-medium">Score</th>
                                    <th className="text-gray-400 font-medium">Status</th>
                                    <th className="text-gray-400 font-medium">Date</th>
                                    <th className="text-gray-400 font-medium w-12"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredEvaluations.map(evaluation => (
                                    <EvaluationRow
                                        key={evaluation.id}
                                        evaluation={evaluation}
                                        onClick={setSelectedEvaluation}
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
        </>
    );
};

export default EvaluationResults;
