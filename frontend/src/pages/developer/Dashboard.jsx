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
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const Dashboard = () => {
    const { user, tenant } = useAuth();
    const navigate = useNavigate();
    const [repos, setRepos] = useState([]);
    const [loading, setLoading] = useState(false);

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

    const chartData = {
        labels: ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5', 'Dec 6', 'Dec 7'],
        datasets: [
            {
                label: 'Critical',
                data: [0, 0, 0, 0, 0, 0, 0],
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                fill: true,
                tension: 0.3,
            },
            {
                label: 'High',
                data: [0, 0, 0, 0, 0, 0, 0],
                borderColor: '#f97316',
                backgroundColor: 'rgba(249, 115, 22, 0.1)',
                fill: true,
                tension: 0.3,
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
                                <button onClick={() => navigate('/dev-dashboard/repositories')} className="text-sm font-medium text-primary hover:underline">View All Scans</button>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead className="bg-white/5">
                                        <tr>
                                            <th className="px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Repository</th>
                                            <th className="px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                                            <th className="px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Details</th>
                                            <th className="px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Added</th>
                                            <th className="px-6 py-3"></th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/10">
                                        {repos.slice(0, 5).map((repo) => (
                                            <tr key={repo.id} className="hover:bg-white/5 transition-colors">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="text-sm font-medium text-white">{repo.name}</div>
                                                    <div className="text-sm text-gray-500">{repo.orgName}</div>
                                                    {repo.description && (
                                                        <div className="text-xs text-gray-600 mt-1 max-w-xs truncate">
                                                            {repo.description}
                                                        </div>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                                        repo.validation_status === 'valid' ? 'bg-green-500/10 text-green-400' :
                                                        repo.validation_status === 'invalid' ? 'bg-red-500/10 text-red-400' :
                                                        repo.validation_status === 'access_denied' ? 'bg-yellow-500/10 text-yellow-400' :
                                                        'bg-gray-500/10 text-gray-400'
                                                    }`}>
                                                        {repo.validation_status ? repo.validation_status.replace('_', ' ').toUpperCase() : 'Pending'}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="flex items-center gap-3 text-sm">
                                                        {repo.primary_language && (
                                                            <span className="text-blue-400">{repo.primary_language}</span>
                                                        )}
                                                        {repo.stars_count > 0 && (
                                                            <span className="text-yellow-400">⭐ {repo.stars_count}</span>
                                                        )}
                                                        {repo.forks_count > 0 && (
                                                            <span className="text-gray-400">🍴 {repo.forks_count}</span>
                                                        )}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {repo.created_at ? new Date(repo.created_at).toLocaleDateString() : 'Unknown'}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                    <a 
                                                        href={repo.url} 
                                                        target="_blank" 
                                                        rel="noopener noreferrer"
                                                        className="text-primary hover:text-blue-400 flex items-center gap-1"
                                                    >
                                                        View Repo <ExternalLink className="w-3 h-3" />
                                                    </a>
                                                </td>
                                            </tr>
                                        ))}
                                        {repos.length === 0 && (
                                            <tr>
                                                <td colSpan="5" className="px-6 py-12 text-center">
                                                    <div className="flex flex-col items-center gap-3">
                                                        <Shield className="w-12 h-12 text-gray-600" />
                                                        <p className="text-gray-400">No repositories assigned yet</p>
                                                        <p className="text-sm text-gray-500">
                                                            Contact your tenant owner to get repository access
                                                        </p>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Vulnerability Trend Chart */}
                        <div className="bg-[#0A0F16] border border-white/10 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">Vulnerability Trend (Last 30 Days)</h3>
                            <div className="h-64 cursor-crosshair">
                                <Line data={chartData} options={chartOptions} />
                            </div>
                        </div>
                    </div>

                    {/* Right Column (1/3) */}
                    <div className="flex flex-col gap-6">
                        {/* Vulnerability Summary */}
                        <div className="bg-[#0A0F16] border border-white/10 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-white mb-6">Vulnerability Summary</h3>
                            <div className="space-y-5">
                                <ProgressBar label="Critical" count={0} color="bg-red-500" width="0%" />
                                <ProgressBar label="High" count={0} color="bg-orange-400" width="0%" />
                                <ProgressBar label="Medium" count={0} color="bg-yellow-500" width="0%" />
                                <ProgressBar label="Low" count={0} color="bg-blue-400" width="0%" />
                            </div>
                            <p className="text-xs text-gray-500 mt-4 text-center">
                                Real data coming in Week 2
                            </p>
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

