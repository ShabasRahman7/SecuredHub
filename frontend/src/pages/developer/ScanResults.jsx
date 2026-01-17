import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Shield, AlertTriangle, AlertCircle, Info, Clock, CheckCircle, XCircle, ChevronDown, ChevronUp, Search, Filter, FileText, Bot } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';

const SEVERITY_CONFIG = {
    critical: {
        bg: 'bg-red-500/10',
        text: 'text-red-400',
        border: 'border-red-500/20',
        icon: AlertCircle,
        badge: 'bg-red-500'
    },
    high: {
        bg: 'bg-orange-500/10',
        text: 'text-orange-400',
        border: 'border-orange-500/20',
        icon: AlertTriangle,
        badge: 'bg-orange-500'
    },
    medium: {
        bg: 'bg-yellow-500/10',
        text: 'text-yellow-400',
        border: 'border-yellow-500/20',
        icon: AlertTriangle,
        badge: 'bg-yellow-500'
    },
    low: {
        bg: 'bg-blue-500/10',
        text: 'text-blue-400',
        border: 'border-blue-500/20',
        icon: Info,
        badge: 'bg-blue-500'
    }
};

const FindingRow = ({ finding, onSelect }) => {
    const config = SEVERITY_CONFIG[finding.severity] || SEVERITY_CONFIG.low;
    const Icon = config.icon;

    return (
        <div
            className={`p-4 border rounded-lg cursor-pointer transition-all hover:scale-[1.01] ${config.bg} ${config.border}`}
            onClick={() => onSelect(finding)}
        >
            <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                        <Icon className={`w-5 h-5 ${config.text}`} />
                        <h3 className="font-semibold text-white">{finding.title}</h3>
                        <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${config.badge} text-white`}>
                            {finding.severity}
                        </span>
                        <span className="px-2 py-0.5 rounded text-xs bg-gray-700 text-gray-300">
                            {finding.tool}
                        </span>
                    </div>
                    <p className="text-sm text-gray-400 mb-2">{finding.description}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                            <FileText className="w-3 h-3" />
                            {finding.file_path}
                        </span>
                        {finding.line_number && <span>Line {finding.line_number}</span>}
                    </div>
                </div>
            </div>
        </div>
    );
};

const FindingDetailModal = ({ finding, onClose }) => {
    if (!finding) return null;
    const navigate = useNavigate();
    const config = SEVERITY_CONFIG[finding.severity] || SEVERITY_CONFIG.low;

    // Extract code snippet from raw_output
    const getCodeSnippet = () => {
        if (!finding.raw_output) return null;

        // some scanners store code in raw_output.code or raw_output.snippet
        if (finding.raw_output.code) {
            return finding.raw_output.code;
        }

        // Some scanners might store it differently
        if (finding.raw_output.snippet) {
            return finding.raw_output.snippet;
        }

        return null;
    };

    const codeSnippet = getCodeSnippet();
    const lineNumber = finding.line_number || 1;

    return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
            <div className="bg-[#0A0F16] rounded-xl border border-white/10 max-w-4xl w-full max-h-[90vh] overflow-auto" onClick={e => e.stopPropagation()}>
                <div className="p-6">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-6">
                        <div className="flex-1">
                            <div className="flex items-center gap-3 mb-3">
                                <span className={`px-3 py-1 rounded font-bold uppercase text-sm ${config.badge} text-white`}>
                                    {finding.severity}
                                </span>
                                <span className="px-3 py-1 rounded bg-gray-700 text-gray-300 text-sm">
                                    {finding.tool}
                                </span>
                                {finding.rule_id && (
                                    <span className="px-3 py-1 rounded bg-gray-800 text-gray-400 text-xs font-mono">
                                        {finding.rule_id}
                                    </span>
                                )}
                            </div>
                            <h2 className="text-xl font-bold text-white mb-2">{finding.title}</h2>
                            <p className="text-gray-400 text-sm leading-relaxed">{finding.description}</p>
                        </div>
                        <button onClick={onClose} className="btn btn-circle btn-sm btn-ghost text-gray-400 hover:text-white">
                            ✕
                        </button>
                    </div>

                    {/* Location */}
                    <div className="bg-[#05080C] border border-white/10 rounded-lg p-4 mb-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <FileText className="w-5 h-5 text-blue-400" />
                                <div>
                                    <p className="text-white font-mono text-sm">{finding.file_path}</p>
                                    {finding.line_number && (
                                        <p className="text-gray-500 text-xs mt-0.5">Line {finding.line_number}</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Code Snippet */}
                    {codeSnippet ? (
                        <div className="mb-4">
                            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                                Vulnerable Code
                            </h3>
                            <div className="bg-[#0d1117] border border-red-500/30 rounded-lg overflow-hidden">
                                <div className="flex items-center gap-2 px-4 py-2 bg-red-500/10 border-b border-red-500/20">
                                    <AlertCircle className="w-4 h-4 text-red-400" />
                                    <span className="text-red-400 text-xs font-medium">Security Issue Detected</span>
                                </div>
                                <div className="p-4 overflow-x-auto">
                                    <pre className="text-sm font-mono">
                                        <code className="text-gray-300">
                                            {codeSnippet.split('\n').map((line, idx) => {
                                                const currentLineNum = lineNumber - Math.floor(codeSnippet.split('\n').length / 2) + idx;
                                                const isVulnerableLine = currentLineNum === lineNumber;
                                                return (
                                                    <div
                                                        key={idx}
                                                        className={`flex ${isVulnerableLine ? 'bg-red-500/20 -mx-4 px-4' : ''}`}
                                                    >
                                                        <span className={`select-none w-12 text-right pr-4 ${isVulnerableLine ? 'text-red-400' : 'text-gray-600'}`}>
                                                            {currentLineNum > 0 ? currentLineNum : ''}
                                                        </span>
                                                        <span className={isVulnerableLine ? 'text-red-300' : ''}>
                                                            {line || ' '}
                                                        </span>
                                                    </div>
                                                );
                                            })}
                                        </code>
                                    </pre>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="bg-[#05080C] border border-white/10 rounded-lg p-6 mb-4 text-center">
                            <FileText className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                            <p className="text-gray-500 text-sm">Code snippet not available</p>
                            <p className="text-gray-600 text-xs mt-1">Click "Ask AI" for detailed analysis</p>
                        </div>
                    )}

                    {/* Additional Security Info - handles Semgrep, Trivy, and legacy formats */}
                    {finding.raw_output && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                            {/* CWE Info - Semgrep format (array) or legacy Bandit format (object) */}
                            {(finding.raw_output.cwe?.length > 0 || finding.raw_output.issue_cwe) && (
                                <div className="bg-[#05080C] border border-white/10 rounded-lg p-3">
                                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">CWE</p>
                                    <div className="flex flex-wrap gap-1">
                                        {finding.raw_output.cwe?.map((cwe, idx) => (
                                            <span key={idx} className="text-blue-400 text-sm font-medium">
                                                {cwe}
                                            </span>
                                        ))}
                                        {finding.raw_output.issue_cwe && (
                                            <span className="text-blue-400 text-sm font-medium">
                                                CWE-{finding.raw_output.issue_cwe.id}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* OWASP Info - Semgrep format */}
                            {finding.raw_output.owasp?.length > 0 && (
                                <div className="bg-[#05080C] border border-white/10 rounded-lg p-3">
                                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">OWASP</p>
                                    <div className="flex flex-wrap gap-1">
                                        {finding.raw_output.owasp.map((owasp, idx) => (
                                            <span key={idx} className="text-purple-400 text-sm font-medium">
                                                {owasp}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Trivy - Package/Version Info */}
                            {finding.raw_output.package_name && (
                                <div className="bg-[#05080C] border border-white/10 rounded-lg p-3">
                                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Package</p>
                                    <p className="text-white text-sm font-medium">{finding.raw_output.package_name}</p>
                                    <p className="text-gray-400 text-xs mt-1">
                                        {finding.raw_output.installed_version}
                                        {finding.raw_output.fixed_version && (
                                            <span className="text-green-400"> → {finding.raw_output.fixed_version}</span>
                                        )}
                                    </p>
                                </div>
                            )}

                            {/* References/Documentation */}
                            {(finding.raw_output.references?.length > 0 || finding.raw_output.more_info) && (
                                <div className="bg-[#05080C] border border-white/10 rounded-lg p-3">
                                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">References</p>
                                    {finding.raw_output.references?.slice(0, 2).map((ref, idx) => (
                                        <a
                                            key={idx}
                                            href={ref}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-400 hover:text-blue-300 text-xs block truncate"
                                        >
                                            {ref.replace(/https?:\/\//, '').substring(0, 40)}...
                                        </a>
                                    ))}
                                    {finding.raw_output.more_info && (
                                        <a
                                            href={finding.raw_output.more_info}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                                        >
                                            Learn More
                                        </a>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Ask AI Assistant Button */}
                    <div className="pt-4 border-t border-white/10">
                        <button
                            onClick={() => navigate(`/dev-dashboard/ai-assistant/${finding.id}`)}
                            className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold rounded-lg flex items-center justify-center gap-3 transition-all transform hover:scale-[1.02]"
                        >
                            <Bot className="w-5 h-5" />
                            <span>Ask AI for Fix Suggestions</span>
                        </button>
                        <p className="text-xs text-gray-500 text-center mt-2">
                            Get AI-powered remediation guidance for this vulnerability
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

const ScanResults = () => {
    const { scanId } = useParams();
    const navigate = useNavigate();
    const [scan, setScan] = useState(null);
    const [findings, setFindings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedFinding, setSelectedFinding] = useState(null);
    const [filters, setFilters] = useState({
        search: '',
        severity: 'all',
        tool: 'all'
    });

    useEffect(() => {
        fetchScanData();
    }, [scanId]);

    const fetchScanData = async () => {
        try {
            const scanResponse = await api.get(`/scans/${scanId}/`);
            setScan(scanResponse.data);

            const findingsResponse = await api.get(`/scans/${scanId}/findings/`);
            setFindings(findingsResponse.data);
        } catch (error) {
            console.error(`Failed to fetch scan ${scanId}:`, error.response?.data || error.message);
            toast.error(`Couldn't load scan results: ${error.response?.status || 'Network error'}`);
        } finally {
            setLoading(false);
        }
    };

    const findingsBySeverity = findings.reduce((acc, finding) => {
        acc[finding.severity] = (acc[finding.severity] || 0) + 1;
        return acc;
    }, { critical: 0, high: 0, medium: 0, low: 0 });

    const toolCounts = findings.reduce((acc, finding) => {
        acc[finding.tool] = (acc[finding.tool] || 0) + 1;
        return acc;
    }, {});

    const filteredFindings = findings.filter(finding => {
        const matchesSearch = finding.title.toLowerCase().includes(filters.search.toLowerCase()) ||
            finding.description.toLowerCase().includes(filters.search.toLowerCase()) ||
            finding.file_path.toLowerCase().includes(filters.search.toLowerCase());
        const matchesSeverity = filters.severity === 'all' || finding.severity === filters.severity;
        const matchesTool = filters.tool === 'all' || finding.tool === filters.tool;
        return matchesSearch && matchesSeverity && matchesTool;
    });

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="loading loading-spinner loading-lg text-blue-500"></div>
                    <p className="mt-4 text-gray-400">Loading scan results...</p>
                </div>
            </div>
        );
    }

    return (
        <>
            <div className="mb-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold mb-2 text-white flex items-center">
                            <Shield className="w-8 h-8 mr-3 text-blue-500" />
                            Scan Results
                        </h1>
                        <p className="text-gray-400">
                            Scan ID: {scanId} • {scan?.repository_name || 'Repository'}
                        </p>
                    </div>
                </div>
            </div>

            {/* Scan Status Card */}
            <div className="bg-[#0A0F16] border border-white/10 rounded-xl p-6 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <p className="text-gray-400 text-sm mb-1">Status</p>
                        <div className="flex items-center gap-2">
                            {scan?.status === 'completed' && (
                                <><CheckCircle className="w-5 h-5 text-green-400" />
                                    <span className="text-green-400 font-semibold">Completed</span></>
                            )}
                            {scan?.status === 'failed' && (
                                <><XCircle className="w-5 h-5 text-red-400" />
                                    <span className="text-red-400 font-semibold">Failed</span></>
                            )}
                            {scan?.status === 'running' && (
                                <><Clock className="w-5 h-5 text-blue-400 animate-spin" />
                                    <span className="text-blue-400 font-semibold">Running</span></>
                            )}
                        </div>
                    </div>
                    <div>
                        <p className="text-gray-400 text-sm mb-1">Total Findings</p>
                        <p className="text-2xl font-bold text-white">{findings.length}</p>
                    </div>
                    <div>
                        <p className="text-gray-400 text-sm mb-1">Commit</p>
                        <p className="text-white font-mono text-sm">{scan?.commit_hash?.substring(0, 7) || 'N/A'}</p>
                    </div>
                    <div>
                        <p className="text-gray-400 text-sm mb-1">Scanned At</p>
                        <p className="text-white text-sm">
                            {scan?.completed_at ? new Date(scan.completed_at).toLocaleString() : 'N/A'}
                        </p>
                    </div>
                </div>
            </div>

            {/* Severity Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {Object.entries(findingsBySeverity).map(([severity, count]) => {
                    const config = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.low;
                    return (
                        <div key={severity} className={`p-4 border rounded-lg ${config.bg} ${config.border}`}>
                            <div className="flex items-center justify-between">
                                <span className={`text-sm font-semibold uppercase ${config.text}`}>{severity}</span>
                                <span className="text-2xl font-bold text-white">{count}</span>
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="bg-[#0A0F16] border border-white/10 rounded-xl p-4 mb-6">
                <div className="flex flex-wrap gap-4">
                    <div className="flex-1 min-w-64">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search findings..."
                                className="w-full pl-10 pr-4 py-2 bg-[#05080C] border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                                value={filters.search}
                                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                            />
                        </div>
                    </div>
                    <select
                        className="select select-bordered bg-[#05080C] border-white/10 text-white"
                        value={filters.severity}
                        onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
                    >
                        <option value="all">All Severities</option>
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                    </select>
                    <select
                        className="select select-bordered bg-[#05080C] border-white/10 text-white"
                        value={filters.tool}
                        onChange={(e) => setFilters({ ...filters, tool: e.target.value })}
                    >
                        <option value="all">All Tools</option>
                        {Object.keys(toolCounts).map(tool => (
                            <option key={tool} value={tool}>{tool} ({toolCounts[tool]})</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Findings List */}
            <div className="bg-[#0A0F16] border border-white/10 rounded-xl p-6">
                <h2 className="text-xl font-bold mb-4 flex items-center text-white">
                    <Shield className="w-5 h-5 mr-2" />
                    Findings ({filteredFindings.length})
                </h2>
                <div className="space-y-3">
                    {filteredFindings.length === 0 && (
                        <div className="text-center py-12">
                            <Shield className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                            <p className="text-gray-400 text-lg">No findings match your filters</p>
                        </div>
                    )}
                    {filteredFindings.map((finding) => (
                        <FindingRow key={finding.id} finding={finding} onSelect={setSelectedFinding} />
                    ))}
                </div>
            </div>

            {selectedFinding && (
                <FindingDetailModal finding={selectedFinding} onClose={() => setSelectedFinding(null)} />
            )}
        </>
    );
};

export default ScanResults;
