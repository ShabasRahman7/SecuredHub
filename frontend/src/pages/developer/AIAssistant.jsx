import { useState, useEffect, useRef } from 'react';
import { Bot, Send, Loader2, Sparkles, ChevronDown, ChevronRight, AlertCircle, Copy, Download, Check, FileCode, ArrowRight, Shield, TrendingUp } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/axios';
import { checkAIHealth, runAgent } from '../../api/services/ai';

const AIAssistant = () => {
    const { tenant } = useAuth();
    const [goal, setGoal] = useState('');
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState(null);
    const [error, setError] = useState(null);
    const [aiAvailable, setAiAvailable] = useState(null);
    const [expandedSteps, setExpandedSteps] = useState(new Set());
    const [evaluations, setEvaluations] = useState([]);
    const [selectedEvalId, setSelectedEvalId] = useState('');
    const [copiedFile, setCopiedFile] = useState(null);
    const inputRef = useRef(null);

    // Check AI health on mount
    useEffect(() => {
        const checkHealth = async () => {
            const health = await checkAIHealth();
            setAiAvailable(health.available);
        };
        checkHealth();
    }, []);

    // Fetch recent evaluations for context
    useEffect(() => {
        const fetchEvaluations = async () => {
            if (!tenant) return;
            try {
                const repoRes = await api.get(`/tenants/${tenant.id}/repositories/`);
                const repos = repoRes.data.repositories || [];

                const allEvals = [];
                for (const repo of repos.slice(0, 5)) {
                    try {
                        const evalRes = await api.get(`/compliance/repositories/${repo.id}/evaluations/`);
                        const repoEvals = (evalRes.data || [])
                            .filter(e => e.status === 'completed')
                            .slice(0, 3)
                            .map(e => ({
                                ...e,
                                repository_name: repo.name
                            }));
                        allEvals.push(...repoEvals);
                    } catch { }
                }
                allEvals.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                setEvaluations(allEvals.slice(0, 10));
            } catch { }
        };
        fetchEvaluations();
    }, [tenant]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!goal.trim() || loading) return;

        setLoading(true);
        setError(null);
        setResponse(null);

        try {
            const result = await runAgent(goal, {
                evaluationId: selectedEvalId ? parseInt(selectedEvalId) : null,
                maxSteps: 5
            });
            setResponse(result);
            setExpandedSteps(new Set([0]));
        } catch (err) {
            console.error('AI Agent error:', err);
            setError(err.response?.data?.detail || err.message || 'AI service error');
        } finally {
            setLoading(false);
        }
    };

    const toggleStep = (index) => {
        const newExpanded = new Set(expandedSteps);
        if (newExpanded.has(index)) {
            newExpanded.delete(index);
        } else {
            newExpanded.add(index);
        }
        setExpandedSteps(newExpanded);
    };

    const copyToClipboard = async (content, filename) => {
        await navigator.clipboard.writeText(content);
        setCopiedFile(filename);
        setTimeout(() => setCopiedFile(null), 2000);
    };

    const downloadFile = (content, filename) => {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename.split('/').pop();
        a.click();
        URL.revokeObjectURL(url);
    };

    // Extract generated files from tool calls
    const getGeneratedFiles = () => {
        if (!response?.tool_calls) return [];
        return response.tool_calls
            .filter(tc => tc.tool_name === 'generate_fix' && tc.result?.success)
            .map(tc => tc.result);
    };

    // Extract score impact data from tool calls
    const getScoreImpact = () => {
        if (!response?.tool_calls) return null;
        const impactCall = response.tool_calls.find(tc => tc.tool_name === 'calculate_impact' && tc.result?.success);
        return impactCall?.result || null;
    };

    const exampleQueries = [
        "What should I fix first to pass SOC2 audit?",
        "Generate a CODEOWNERS file for my repo",
        "How can I improve my compliance score?",
        "Create a dependabot.yml for Python and JavaScript"
    ];

    const generatedFiles = getGeneratedFiles();
    const scoreImpact = getScoreImpact();

    return (
        <>
            {/* Header */}
            <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
                <div className="flex min-w-72 flex-col gap-1">
                    <h1 className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight flex items-center gap-3">
                        <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-xl">
                            <Bot className="w-6 h-6 text-white" />
                        </div>
                        AI Compliance Assistant
                    </h1>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        Get AI-powered fixes with exact score projections and ready-to-commit files.
                    </p>
                </div>

                {/* Status Indicator */}
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium
                    ${aiAvailable === null ? 'bg-gray-500/10 text-gray-400' :
                        aiAvailable ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                            'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                    <span className={`w-2 h-2 rounded-full ${aiAvailable === null ? 'bg-gray-400' :
                        aiAvailable ? 'bg-green-400 animate-pulse' : 'bg-red-400'
                        }`} />
                    {aiAvailable === null ? 'Checking...' :
                        aiAvailable ? 'AI Online' : 'AI Offline'}
                </div>
            </div>

            {/* Main Content */}
            <div className="grid lg:grid-cols-3 gap-6">
                {/* Input Section */}
                <div className="lg:col-span-2 space-y-4">
                    {/* Query Form */}
                    <div className="bg-[#0A0F16] border border-white/10 rounded-xl p-6">
                        <form onSubmit={handleSubmit} className="space-y-4">
                            {/* Evaluation Context Selector */}
                            {evaluations.length > 0 && (
                                <div>
                                    <label className="text-sm text-gray-400 mb-2 block">
                                        Select evaluation for analysis
                                    </label>
                                    <select
                                        value={selectedEvalId}
                                        onChange={(e) => setSelectedEvalId(e.target.value)}
                                        className="w-full bg-[#05080C] border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary/50"
                                    >
                                        <option value="">No specific evaluation</option>
                                        {evaluations.map(e => (
                                            <option key={e.id} value={e.id}>
                                                #{e.id} - {e.repository_name} ({e.score?.toFixed(1) || 0}%)
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            )}

                            {/* Goal Input */}
                            <div>
                                <label className="text-sm text-gray-400 mb-2 block">
                                    What would you like to know or generate?
                                </label>
                                <div className="relative">
                                    <textarea
                                        ref={inputRef}
                                        value={goal}
                                        onChange={(e) => setGoal(e.target.value)}
                                        placeholder="e.g., 'What should I fix first to pass SOC2?' or 'Generate a CODEOWNERS file'"
                                        className="w-full bg-[#05080C] border border-white/10 rounded-lg px-4 py-3 pr-12 text-white placeholder-gray-500 focus:outline-none focus:border-primary/50 resize-none"
                                        rows={3}
                                        disabled={loading || !aiAvailable}
                                    />
                                    <button
                                        type="submit"
                                        disabled={loading || !goal.trim() || !aiAvailable}
                                        className="absolute right-3 bottom-3 p-2 rounded-lg bg-primary hover:bg-primary/80 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
                                    >
                                        {loading ? (
                                            <Loader2 className="w-5 h-5 animate-spin text-white" />
                                        ) : (
                                            <Send className="w-5 h-5 text-white" />
                                        )}
                                    </button>
                                </div>
                            </div>
                        </form>

                        {/* Example Queries */}
                        <div className="mt-4 pt-4 border-t border-white/5">
                            <p className="text-xs text-gray-500 mb-2">Try asking:</p>
                            <div className="flex flex-wrap gap-2">
                                {exampleQueries.map((query, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => setGoal(query)}
                                        className="text-xs px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-gray-400 hover:text-white transition-colors"
                                    >
                                        {query}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Error Display */}
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-red-400 font-medium">Analysis Failed</p>
                                <p className="text-red-400/70 text-sm mt-1">{error}</p>
                            </div>
                        </div>
                    )}

                    {/* Response Display */}
                    {response && (
                        <div className="space-y-4">
                            {/* Score Impact Card */}
                            {scoreImpact && (
                                <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-white/10 rounded-xl p-5">
                                    <div className="flex items-center gap-3 mb-4">
                                        <TrendingUp className="w-5 h-5 text-green-400" />
                                        <h3 className="text-white font-semibold">Score Impact Analysis</h3>
                                    </div>

                                    <div className="flex items-center gap-4 mb-4">
                                        <div className="text-center">
                                            <div className="text-3xl font-bold text-red-400">{scoreImpact.current_score}%</div>
                                            <div className="text-xs text-gray-400">Current</div>
                                        </div>
                                        <ArrowRight className="w-6 h-6 text-gray-500" />
                                        <div className="text-center">
                                            <div className="text-3xl font-bold text-green-400">{scoreImpact.total_if_all_fixed}%</div>
                                            <div className="text-xs text-gray-400">Potential</div>
                                        </div>
                                    </div>

                                    {/* Fix Priority List */}
                                    <div className="space-y-2">
                                        {scoreImpact.fixes?.slice(0, 5).map((fix, idx) => (
                                            <div key={idx} className="flex items-center gap-3 bg-black/20 rounded-lg p-3">
                                                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                                                    ${idx === 0 ? 'bg-red-500/20 text-red-400' :
                                                        idx === 1 ? 'bg-orange-500/20 text-orange-400' :
                                                            'bg-yellow-500/20 text-yellow-400'}`}>
                                                    {idx + 1}
                                                </span>
                                                <div className="flex-1 min-w-0">
                                                    <div className="text-sm text-white font-medium truncate">{fix.rule_name}</div>
                                                    <div className="flex items-center gap-2 text-xs text-gray-400">
                                                        {fix.soc2?.map(c => (
                                                            <span key={c} className="px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded">SOC2: {c}</span>
                                                        ))}
                                                        {fix.iso27001?.slice(0, 1).map(c => (
                                                            <span key={c} className="px-1.5 py-0.5 bg-purple-500/20 text-purple-400 rounded">ISO: {c}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-sm font-bold text-green-400">+{fix.impact_percent}%</div>
                                                    <div className="text-xs text-gray-500">{fix.score_before}% → {fix.score_after}%</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Generated Files */}
                            {generatedFiles.length > 0 && (
                                <div className="bg-[#0A0F16] border border-green-500/20 rounded-xl overflow-hidden">
                                    <div className="p-4 bg-green-500/10 border-b border-green-500/20 flex items-center gap-3">
                                        <FileCode className="w-5 h-5 text-green-400" />
                                        <div>
                                            <p className="text-white font-medium">Generated Files</p>
                                            <p className="text-gray-400 text-xs">{generatedFiles.length} file(s) ready to commit</p>
                                        </div>
                                    </div>

                                    <div className="divide-y divide-white/5">
                                        {generatedFiles.map((file, idx) => (
                                            <div key={idx} className="p-4">
                                                <div className="flex items-center justify-between mb-3">
                                                    <div className="flex items-center gap-2">
                                                        <code className="text-sm text-green-400 bg-green-500/10 px-2 py-1 rounded">
                                                            {file.filename}
                                                        </code>
                                                        {file.framework_mapping?.soc2?.map(c => (
                                                            <span key={c} className="text-xs px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded">
                                                                SOC2: {c}
                                                            </span>
                                                        ))}
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => copyToClipboard(file.content, file.filename)}
                                                            className="flex items-center gap-1 px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-gray-300 transition-colors"
                                                        >
                                                            {copiedFile === file.filename ? (
                                                                <><Check className="w-4 h-4 text-green-400" /> Copied!</>
                                                            ) : (
                                                                <><Copy className="w-4 h-4" /> Copy</>
                                                            )}
                                                        </button>
                                                        <button
                                                            onClick={() => downloadFile(file.content, file.filename)}
                                                            className="flex items-center gap-1 px-3 py-1.5 bg-primary/20 hover:bg-primary/30 rounded-lg text-sm text-primary transition-colors"
                                                        >
                                                            <Download className="w-4 h-4" /> Download
                                                        </button>
                                                    </div>
                                                </div>
                                                <pre className="bg-[#05080C] rounded-lg p-4 overflow-x-auto text-sm text-gray-300 font-mono max-h-64 overflow-y-auto">
                                                    <code>{file.content}</code>
                                                </pre>
                                                <p className="mt-2 text-xs text-gray-500">{file.instructions}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Main Response */}
                            <div className="bg-[#0A0F16] border border-white/10 rounded-xl overflow-hidden">
                                {/* Response Header */}
                                <div className="p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-b border-white/10">
                                    <div className="flex items-center gap-3">
                                        <Sparkles className="w-5 h-5 text-purple-400" />
                                        <div>
                                            <p className="text-white font-medium">AI Analysis</p>
                                            <p className="text-gray-400 text-sm">
                                                {response.steps_taken} steps • {response.tool_calls?.length || 0} tools
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* Main Result */}
                                <div className="p-4">
                                    <div className="prose prose-invert max-w-none">
                                        <div className="text-gray-200 whitespace-pre-wrap leading-relaxed">
                                            {response.result}
                                        </div>
                                    </div>
                                </div>

                                {/* Reasoning Steps */}
                                {response.reasoning_steps?.length > 0 && (
                                    <div className="border-t border-white/10">
                                        <div className="p-4">
                                            <p className="text-sm text-gray-400 mb-3 flex items-center gap-2">
                                                <Bot className="w-4 h-4" />
                                                Reasoning Trace
                                            </p>
                                            <div className="space-y-2">
                                                {response.reasoning_steps.map((step, idx) => (
                                                    <div key={idx} className="bg-[#05080C] rounded-lg overflow-hidden">
                                                        <button
                                                            onClick={() => toggleStep(idx)}
                                                            className="w-full flex items-center gap-3 p-3 text-left hover:bg-white/5 transition-colors"
                                                        >
                                                            {expandedSteps.has(idx) ? (
                                                                <ChevronDown className="w-4 h-4 text-gray-500" />
                                                            ) : (
                                                                <ChevronRight className="w-4 h-4 text-gray-500" />
                                                            )}
                                                            <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded">
                                                                Step {step.step_number}
                                                            </span>
                                                            <span className="text-sm text-gray-300 truncate">
                                                                {step.thought}
                                                            </span>
                                                        </button>
                                                        {expandedSteps.has(idx) && (step.action || step.observation) && (
                                                            <div className="px-10 pb-3 space-y-2">
                                                                {step.action && (
                                                                    <p className="text-xs text-gray-500">
                                                                        <span className="text-purple-400">Action:</span> {step.action}
                                                                    </p>
                                                                )}
                                                                {step.observation && (
                                                                    <p className="text-xs text-gray-500 font-mono bg-black/30 p-2 rounded overflow-x-auto">
                                                                        {step.observation.substring(0, 200)}
                                                                        {step.observation.length > 200 && '...'}
                                                                    </p>
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Sidebar */}
                <div className="space-y-4">
                    {/* About Card */}
                    <div className="bg-[#0A0F16] border border-white/10 rounded-xl p-5">
                        <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                            <Shield className="w-4 h-4 text-blue-400" />
                            Compliance AI Agent
                        </h3>
                        <p className="text-gray-400 text-sm leading-relaxed">
                            Powered by LLaMA 3.3-70B with SOC2 and ISO-27001 knowledge base.
                        </p>
                        <div className="mt-4 space-y-2">
                            <div className="flex items-center gap-2 text-sm text-gray-400">
                                <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                                Score impact prediction
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-400">
                                <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                                SOC2/ISO-27001 mapping
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-400">
                                <div className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                                Fix file generation
                            </div>
                        </div>
                    </div>

                    {/* Capabilities */}
                    <div className="bg-[#0A0F16] border border-white/10 rounded-xl p-5">
                        <h3 className="text-white font-semibold mb-3">What I can generate</h3>
                        <ul className="space-y-2 text-sm text-gray-400">
                            <li className="flex items-center gap-2">
                                <FileCode className="w-4 h-4 text-green-400" />
                                CODEOWNERS file
                            </li>
                            <li className="flex items-center gap-2">
                                <FileCode className="w-4 h-4 text-green-400" />
                                dependabot.yml
                            </li>
                            <li className="flex items-center gap-2">
                                <FileCode className="w-4 h-4 text-green-400" />
                                SECURITY.md
                            </li>
                            <li className="flex items-center gap-2">
                                <FileCode className="w-4 h-4 text-green-400" />
                                README.md
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </>
    );
};

export default AIAssistant;
