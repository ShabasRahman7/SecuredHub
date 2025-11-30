import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import DeveloperSidebar from '../../components/developer/DeveloperSidebar';
import { Search, Bell, Menu, ExternalLink, Play, Bot, Shield } from 'lucide-react';
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

const DevDashboard = () => {
    const { user, tenants, logout } = useAuth();
    const [activeTab, setActiveTab] = useState('dashboard');
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [repos, setRepos] = useState([]);
    const [loading, setLoading] = useState(false);

    // Fetch Repositories - Parallel API calls for better performance
    useEffect(() => {
        const fetchRepos = async () => {
            if (tenants.length === 0) return;
            setLoading(true);
            try {
                // Make parallel requests instead of sequential
                const promises = tenants.map(org => 
                    api.get(`/tenants/${org.id}/repositories/`)
                        .catch(err => {
                            console.error(`Failed to fetch repos for ${org.name}:`, err);
                            return { data: { repositories: [] } };
                        })
                );
                const results = await Promise.all(promises);
                const allRepos = results.flatMap((res, i) => 
                    res.data.repositories.map(r => ({ 
                        ...r, 
                        orgName: tenants[i].name,
                        orgId: tenants[i].id 
                    }))
                );
                setRepos(allRepos);
            } catch (error) {
                console.error('Failed to fetch repositories:', error);
                toast.error('Failed to load repositories');
            } finally {
                setLoading(false);
            }
        };
        fetchRepos();
    }, [tenants]);

    const handleScan = () => {
        toast.info('Scan functionality coming in Week 2');
    };

    // Chart Options
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

    // Chart Data - Will be replaced with real data from backend in Week 2
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

    return (
        <div className="flex h-screen w-full bg-[#05080C] text-white font-sans overflow-hidden">

            {/* Sidebar */}
            <DeveloperSidebar
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                logout={logout}
                user={user}
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
            />

            {/* Main Content */}
            <div className="flex flex-1 flex-col overflow-y-auto relative w-full">

                {/* Header */}
                <header className="flex sticky top-0 z-10 items-center justify-between whitespace-nowrap border-b border-white/10 px-6 py-3 bg-[#05080C]/80 backdrop-blur-sm">
                    <div className="flex items-center gap-4 lg:gap-8">
                        <button
                            className="lg:hidden p-2 -ml-2 text-gray-400 hover:text-white"
                            onClick={() => setSidebarOpen(true)}
                        >
                            <Menu className="w-6 h-6" />
                        </button>
                        <div className="flex items-center gap-2">
                            <h2 className="text-lg font-bold leading-tight text-white">Developer Dashboard</h2>
                            <div className="hidden md:flex items-center gap-2 pl-2 border-l border-white/10">
                                <UsersIconGroup />
                                <span className="text-sm font-medium text-white">
                                    {tenants.length === 1 
                                        ? tenants[0].name 
                                        : tenants.length > 1 
                                        ? `${tenants.length} Organizations` 
                                        : 'No Organization'
                                    }
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-1 justify-end gap-3 lg:gap-4 items-center">
                        <label className="hidden md:flex flex-col min-w-40 !h-10 max-w-64">
                            <div className="flex w-full flex-1 items-stretch rounded-lg h-full bg-[#0A0F16] border border-white/10 focus-within:ring-2 focus-within:ring-primary/50 transition-shadow">
                                <div className="text-gray-400 flex items-center justify-center pl-3">
                                    <Search className="w-5 h-5" />
                                </div>
                                <input className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg bg-transparent h-full placeholder:text-gray-500 pl-2 text-base outline-none border-none text-white" placeholder="Search my repositories..." />
                            </div>
                        </label>
                        <button className="hidden sm:flex cursor-pointer items-center justify-center rounded-full h-10 w-10 text-gray-400 hover:bg-white/10 hover:text-primary border border-transparent hover:border-white/10 transition-all">
                            <Bell className="w-5 h-5" />
                        </button>
                        <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 bg-primary/20 flex items-center justify-center text-primary font-bold">
                            {user?.first_name?.[0]}
                        </div>
                    </div>
                </header>

                <main className="flex-1 p-4 lg:p-8">
                    <div className="max-w-7xl mx-auto space-y-6">

                        {loading && (
                            <div className="flex items-center justify-center py-12">
                                <span className="loading loading-spinner loading-lg text-primary"></span>
                            </div>
                        )}

                        {!loading && activeTab === 'dashboard' && (
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                {/* Left Column (2/3) */}
                                <div className="lg:col-span-2 flex flex-col gap-6">

                                    {/* Recent Scans Table */}
                                    <div className="bg-[#0A0F16] border border-white/10 rounded-xl overflow-hidden">
                                        <div className="flex justify-between items-center px-6 py-4 border-b border-white/10">
                                            <h2 className="text-lg font-semibold text-white">Recent Scans on My Repositories</h2>
                                            <button onClick={() => setActiveTab('repositories')} className="text-sm font-medium text-primary hover:underline">View All Scans</button>
                                        </div>
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-left">
                                                <thead className="bg-white/5">
                                                    <tr>
                                                        <th className="px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Repository</th>
                                                        <th className="px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Scan Status</th>
                                                        <th className="px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Vulnerabilities</th>
                                                        <th className="px-6 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Completed</th>
                                                        <th className="px-6 py-3"></th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-white/10">
                                                    {repos.slice(0, 5).map((repo) => (
                                                        <tr key={repo.id} className="hover:bg-white/5 transition-colors">
                                                            <td className="px-6 py-4 whitespace-nowrap">
                                                                <div className="text-sm font-medium text-white">{repo.name}</div>
                                                                <div className="text-sm text-gray-500">{repo.orgName}</div>
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap">
                                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                                                    repo.last_scan_status === 'failed' ? 'bg-red-500/10 text-red-400' :
                                                                    repo.last_scan_status === 'in_progress' ? 'bg-yellow-500/10 text-yellow-400' :
                                                                    repo.last_scan_status === 'completed' ? 'bg-green-500/10 text-green-400' :
                                                                    'bg-gray-500/10 text-gray-400'
                                                                }`}>
                                                                    {repo.last_scan_status ? repo.last_scan_status.replace('_', ' ').toUpperCase() : 'Not Scanned'}
                                                                </span>
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap">
                                                                <div className="flex items-center gap-3 text-sm text-gray-500">
                                                                    <span>Coming Soon</span>
                                                                </div>
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                                {repo.last_scan_at ? new Date(repo.last_scan_at).toLocaleDateString() : 'Never'}
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                                <button className="text-gray-500 cursor-not-allowed" disabled>View Details</button>
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
                                        <button onClick={() => setActiveTab('ai-assistant')} className="w-full flex items-center justify-center gap-2 rounded-lg bg-primary hover:bg-blue-600 transition-colors h-10 px-4 text-sm font-medium text-white">
                                            Ask AI Assistant
                                        </button>
                                    </div>

                                </div>
                            </div>
                        )}

                        {!loading && activeTab === 'repositories' && (
                            <div className="bg-[#0A0F16] shadow-xl rounded-xl border border-white/10 p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center text-white">
                                    <ExternalLink className="w-5 h-5 mr-2" /> Assigned Repositories ({repos.length})
                                </h2>
                                <div className="space-y-4">
                                    {repos.map(repo => (
                                        <div key={repo.id} className="flex flex-col md:flex-row items-center justify-between p-4 bg-[#05080C] border border-white/10 rounded-lg gap-4">
                                            <div className="flex-1">
                                                <h3 className="font-bold text-lg text-white">{repo.name}</h3>
                                                <p className="text-xs text-gray-500 mb-1">Tenant: {repo.orgName}</p>
                                                <a href={repo.url} target="_blank" rel="noreferrer" className="text-sm hover:underline flex items-center text-blue-400">
                                                    {repo.url} <ExternalLink className="w-3 h-3 ml-1" />
                                                </a>
                                            </div>
                                            <div className="flex items-center gap-4">
                                                <div className="text-right">
                                                    <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${
                                                        repo.last_scan_status === 'completed' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                                        repo.last_scan_status === 'failed' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                                        repo.last_scan_status === 'in_progress' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                                                        'bg-gray-500/10 text-gray-400 border-gray-500/20'
                                                    }`}>
                                                        {repo.last_scan_status ? repo.last_scan_status.replace('_', ' ').toUpperCase() : 'Not Scanned'}
                                                    </span>
                                                    <div className="text-xs text-gray-500 mt-1">
                                                        {repo.last_scan_at ? `Scanned ${new Date(repo.last_scan_at).toLocaleDateString()}` : 'Never scanned'}
                                                    </div>
                                                </div>
                                                <button
                                                    className="btn btn-sm bg-gray-700 border-gray-600 text-gray-400 cursor-not-allowed"
                                                    onClick={handleScan}
                                                    disabled
                                                    title="Scan functionality coming in Week 2"
                                                >
                                                    <Play className="w-4 h-4 mr-1" />
                                                    Coming Soon
                                                </button>
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

                        {!loading && (activeTab !== 'dashboard' && activeTab !== 'repositories') && (
                            <div className="flex flex-col items-center justify-center h-96 bg-[#0A0F16] border border-white/10 rounded-xl text-center p-8">
                                <div className="bg-white/5 p-4 rounded-full mb-4">
                                    {activeTab === 'vulnerabilities' && <Shield className="w-12 h-12 text-gray-400" />}
                                    {activeTab === 'ai-assistant' && <Bot className="w-12 h-12 text-gray-400" />}
                                    {activeTab === 'settings' && <Search className="w-12 h-12 text-gray-400" />}
                                </div>
                                <h3 className="text-xl font-bold mb-2 text-white capitalize">{activeTab.replace('-', ' ')}</h3>
                                <p className="text-gray-500">This module is coming soon in Week 2.</p>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
};

// --- Sub-components to keep code clean ---

const UsersIconGroup = () => (
    <div className="flex -space-x-1 overflow-hidden">
        <div className="inline-block h-4 w-4 rounded-full ring-2 ring-[#05080C] bg-gray-500 flex items-center justify-center text-[8px] text-white">OA</div>
    </div>
);

const ProgressBar = ({ label, count, color, width }) => (
    <div>
        <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">{label}</span>
            <span className={`text-sm font-bold ${color.replace('bg-', 'text-')}`}>{count}</span>
        </div>
        <div className="w-full bg-[#05080C] rounded-full h-2">
            <div className={`${color} h-2 rounded-full`} style={{ width }}></div>
        </div>
    </div >
);

export default DevDashboard;
