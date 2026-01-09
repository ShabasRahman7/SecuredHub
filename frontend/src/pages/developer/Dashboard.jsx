import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { ExternalLink, Play, Bot, Shield } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

const Dashboard = () => {
    const { user, tenant } = useAuth();
    const navigate = useNavigate();
    const [repos, setRepos] = useState([]);
    const [loading, setLoading] = useState(false);
    const [scans, setScans] = useState([]);
    const [vulnerabilityCounts, setVulnerabilityCounts] = useState({
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
    });

    useEffect(() => {
        const fetchRepos = async () => {
            if (!tenant) return;
            setLoading(true);
            try {
                const response = await api.get(`/tenants/${tenant.id}/repositories/`);
                const repositories = response.data.repositories || [];
                const reposWithTenant = repositories.map(r => ({
                    ...r,
                    orgName: tenant.name,
                    orgId: tenant.id
                }));
                setRepos(reposWithTenant);

                const allScans = [];
                const severityCounts = { critical: 0, high: 0, medium: 0, low: 0 };

                for (const repo of reposWithTenant) {
                    try {
                        const scanResponse = await api.get(`/scans/repository/${repo.id}/`);
                        const repoScans = scanResponse.data || [];

                        for (const scan of repoScans) {
                            if (scan.status === 'completed') {
                                try {
                                    const findingsResponse = await api.get(`/scans/${scan.id}/findings/`);
                                    const findings = findingsResponse.data || [];

                                    findings.forEach(finding => {
                                        if (severityCounts[finding.severity] !== undefined) {
                                            severityCounts[finding.severity]++;
                                        }
                                    });

                                    allScans.push({
                                        ...scan,
                                        repository_name: repo.name,
                                        findings_count: findings.length
                                    });
                                } catch (err) {
                                }
                            }
                        }
                    } catch (err) {
                    }
                }

                allScans.sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at));
                setScans(allScans.slice(0, 5));
                setVulnerabilityCounts(severityCounts);

            } catch (error) {
                console.error('Failed to fetch repositories:', error);
                toast.error('Failed to load repositories');
                setRepos([]);
            } finally {
                setLoading(false);
            }
        };
        fetchRepos();
    }, [tenant]);

    const handleScan = () => {
        toast.info('Scan functionality coming in Week 2');
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: { color: '#9ca3af', usePointStyle: true, boxWidth: 8 }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: '#1c2027',
                titleColor: '#e2e8f0',
                bodyColor: '#e2e8f0',
                borderColor: 'rgba(59, 69, 84, 0.5)',
                borderWidth: 1,
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: 'rgba(59, 69, 84, 0.5)', borderDash: [3, 3] },
                ticks: { color: '#9ca3af' }
            },
            x: {
                grid: { display: false },
                ticks: { color: '#9ca3af' }
            }
        }
    };

    const totalVulns = vulnerabilityCounts.critical + vulnerabilityCounts.high +
        vulnerabilityCounts.medium + vulnerabilityCounts.low;

    const chartData = {
        labels: ['Critical', 'High', 'Medium', 'Low'],
        datasets: [
            {
                label: 'Vulnerabilities',
                data: [
                    vulnerabilityCounts.critical,
                    vulnerabilityCounts.high,
                    vulnerabilityCounts.medium,
                    vulnerabilityCounts.low
                ],
                backgroundColor: [
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(249, 115, 22, 0.8)',
                    'rgba(251, 191, 36, 0.8)',
                    'rgba(96, 165, 250, 0.8)'
                ],
                borderColor: [
                    '#ef4444',
                    '#f97316',
                    '#fbbf24',
                    '#60a5fa'
                ],
                borderWidth: 1,
                borderRadius: 4
            }
        ]
    };

    const ProgressBar = ({ label, count, color, width }) => (
        <div>
            <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">{label}</span>
                <span className={`text-sm font-bold ${color.replace('bg-', 'text-')}`}>{count}</span>
            </div>
            <div className="w-full bg-[#05080C] rounded-full h-2">
                <div className={`${color} h-2 rounded-full`} style={{ width }}></div>
            </div>
        </div>
    );

    return (
        <>
            {loading && (
                <div className="flex items-center justify-center py-12">
                    <span className="loading loading-spinner loading-lg text-primary"></span>
                </div>
            )}

            {!loading && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left Column (2/3) */}
                    <div className="lg:col-span-2 flex flex-col gap-6">
                        {/* Recent Scans Table */}
                        <div className="bg-[#0A0F16] border border-white/10 rounded-xl overflow-hidden">
                            <div className="flex justify-between items-center px-6 py-4 border-b border-white/10">
                                <h2 className="text-lg font-semibold text-white">Recent Scans on My Repositories</h2>
                                <button onClick={() => navigate('/dev-dashboard/repositories')} className="text-sm font-medium text-primary hover:underline">View All Repositories</button>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead className="bg-white/5">
                                        <tr>
                                            <th className="px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Repository</th>
                                            <th className="px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                                            <th className="px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Findings</th>
                                            <th className="px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Completed</th>
                                            <th className="px-6 py-3"></th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/10">
                                        {scans.map((scan) => (
                                            <tr key={scan.id} className="hover:bg-white/5 transition-colors">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="text-sm font-medium text-white">{scan.repository_name}</div>
                                                    <div className="text-xs text-gray-500">Scan #{scan.id}</div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400">
                                                        {scan.status.toUpperCase()}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={`text-sm font-semibold ${scan.findings_count > 0 ? 'text-orange-400' : 'text-green-400'}`}>
                                                        {scan.findings_count} {scan.findings_count === 1 ? 'finding' : 'findings'}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {scan.completed_at ? new Date(scan.completed_at).toLocaleString() : 'N/A'}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                    <button
                                                        onClick={() => navigate(`/dev-dashboard/scans/${scan.id}`)}
                                                        className="text-primary hover:text-blue-400"
                                                    >
                                                        View Results
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                        {scans.length === 0 && (
                                            <tr>
                                                <td colSpan="5" className="px-6 py-12 text-center">
                                                    <div className="flex flex-col items-center gap-3">
                                                        <Shield className="w-12 h-12 text-gray-600" />
                                                        <p className="text-gray-400">No scans completed yet</p>
                                                        <p className="text-sm text-gray-500">
                                                            Trigger your first scan from the Repositories page
                                                        </p>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* vulnerability chart */}
                        <div className="bg-[#0A0F16] border border-white/10 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">Vulnerability Distribution</h3>
                            <div className="h-64">
                                <Bar data={chartData} options={chartOptions} />
                            </div>
                        </div>
                    </div>

                    {/* Right Column (1/3) */}
                    <div className="flex flex-col gap-6">
                        {/* Vulnerability Summary */}
                        <div className="bg-[#0A0F16] border border-white/10 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-6">Vulnerability Summary</h3>
                            <div className="space-y-5">
                                <ProgressBar
                                    label="Critical"
                                    count={vulnerabilityCounts.critical}
                                    color="bg-red-500"
                                    width={totalVulns > 0 ? `${(vulnerabilityCounts.critical / totalVulns * 100).toFixed(0)}%` : '0%'}
                                />
                                <ProgressBar
                                    label="High"
                                    count={vulnerabilityCounts.high}
                                    color="bg-orange-400"
                                    width={totalVulns > 0 ? `${(vulnerabilityCounts.high / totalVulns * 100).toFixed(0)}%` : '0%'}
                                />
                                <ProgressBar
                                    label="Medium"
                                    count={vulnerabilityCounts.medium}
                                    color="bg-yellow-500"
                                    width={totalVulns > 0 ? `${(vulnerabilityCounts.medium / totalVulns * 100).toFixed(0)}%` : '0%'}
                                />
                                <ProgressBar
                                    label="Low"
                                    count={vulnerabilityCounts.low}
                                    color="bg-blue-400"
                                    width={totalVulns > 0 ? `${(vulnerabilityCounts.low / totalVulns * 100).toFixed(0)}%` : '0%'}
                                />
                            </div>
                            {totalVulns === 0 && (
                                <p className="text-xs text-gray-500 mt-4 text-center">
                                    No vulnerabilities detected yet
                                </p>
                            )}
                        </div>

                        {/* AI Assistant Promo */}
                        <div className="rounded-xl p-6 bg-primary/10 border border-primary/30 flex flex-col items-center text-center">
                            <Bot className="w-10 h-10 text-primary mb-3" />
                            <h3 className="text-lg font-bold text-white">Need help with a vulnerability?</h3>
                            <p className="text-sm text-gray-400 mt-1 mb-6">Our AI assistant can provide explanations and suggest remediation steps.</p>
                            <button onClick={() => navigate('/dev-dashboard/ai-assistant')} className="w-full flex items-center justify-center gap-2 rounded-lg bg-primary hover:bg-blue-600 transition-colors h-10 px-4 text-sm font-medium text-white">
                                Ask AI Assistant
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default Dashboard;


