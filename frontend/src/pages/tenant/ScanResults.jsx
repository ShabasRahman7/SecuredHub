import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Shield, AlertTriangle, AlertCircle, Info, Clock, CheckCircle, XCircle, Search, FileText, ArrowLeft } from 'lucide-react';
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

const FindingCard = ({ finding }) => {
    const config = SEVERITY_CONFIG[finding.severity] || SEVERITY_CONFIG.low;
    const Icon = config.icon;

    return (
        <div className={`p-4 border rounded-lg ${config.bg} ${config.border}`}>
            <div className="flex items-start gap-4">
                <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2 flex-wrap">
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

const ScanResults = () => {
    const { scanId } = useParams();
    const navigate = useNavigate();
    const [scan, setScan] = useState(null);
    const [findings, setFindings] = useState([]);
    const [loading, setLoading] = useState(true);
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
            {/* header */}
            <div className="mb-6">
                <button
                    onClick={() => navigate('/tenant-dashboard/scans')}
                    className="flex items-center gap-2 text-gray-400 hover:text-white mb-4 transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" />
                    <span>Back to Scans</span>
                </button>
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

            {/* scan status card */}
            <div className="bg-[#0A0F16] border border-white/10 rounded-xl p-6 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
                        <p className="text-gray-400 text-sm mb-1">Started</p>
                        <p className="text-white text-sm">
                            {scan?.started_at ? new Date(scan.started_at).toLocaleString() : 'N/A'}
                        </p>
                    </div>
                    <div>
                        <p className="text-gray-400 text-sm mb-1">Completed</p>
                        <p className="text-white text-sm">
                            {scan?.completed_at ? new Date(scan.completed_at).toLocaleString() : 'N/A'}
                        </p>
                    </div>
                </div>
            </div>

            {/* severity stats */}
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

            {/* filters */}
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

            {/* findings list */}
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
                        <FindingCard key={finding.id} finding={finding} />
                    ))}
                </div>
            </div>

            {/* info note for tenant owners */}
            <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <p className="text-sm text-blue-300">
                    <strong>Note:</strong> Developers assigned to this repository can use the AI Assistant to get remediation guidance for these findings.
                </p>
            </div>
        </>
    );
};

export default ScanResults;
