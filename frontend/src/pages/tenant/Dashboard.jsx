import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Link as LinkIcon, Shield, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import api from '../../api/axios';

const Dashboard = () => {
    const { user, tenant } = useAuth();
    const navigate = useNavigate();
    const [currentTenant, setCurrentTenant] = useState(null);
    const [members, setMembers] = useState([]);
    const [repositories, setRepositories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [scanStats, setScanStats] = useState({
        totalScans: 0,
        completedScans: 0,
        vulnerabilities: { critical: 0, high: 0, medium: 0, low: 0 }
    });

    useEffect(() => {
        if (tenant) {
            setCurrentTenant(tenant);
        }
    }, [tenant]);

    useEffect(() => {
        if (currentTenant) {
            fetchDashboardData();
        }
    }, [currentTenant]);

    const fetchDashboardData = async () => {
        if (!currentTenant) return;
        setLoading(true);
        try {
            const [membersRes, reposRes] = await Promise.all([
                api.get(`/tenants/${currentTenant.id}/members/`),
                api.get(`/tenants/${currentTenant.id}/repositories/`)
            ]);

            setMembers(membersRes.data.members || []);
            const repos = reposRes.data.repositories || [];
            setRepositories(repos);

            // fetch scan data for all repositories
            let totalScans = 0;
            let completedScans = 0;
            const vulnerabilities = { critical: 0, high: 0, medium: 0, low: 0 };

            for (const repo of repos) {
                try {
                    const scansRes = await api.get(`/scans/repository/${repo.id}/`);
                    const scans = scansRes.data || [];
                    totalScans += scans.length;

                    for (const scan of scans) {
                        if (scan.status === 'completed') {
                            completedScans++;
                            try {
                                const findingsRes = await api.get(`/scans/${scan.id}/findings/`);
                                const findings = findingsRes.data || [];
                                findings.forEach(f => {
                                    if (vulnerabilities[f.severity] !== undefined) {
                                        vulnerabilities[f.severity]++;
                                    }
                                });
                            } catch (err) {
                                // findings fetch failed, continue
                            }
                        }
                    }
                } catch (err) {
                    // scans fetch failed for this repo
                }
            }

            setScanStats({ totalScans, completedScans, vulnerabilities });
        } catch (error) {
            console.error('Failed to fetch dashboard data', error);
        } finally {
            setLoading(false);
        }
    };

    if (!currentTenant || loading) {
        return (
            <div className="h-screen flex flex-col items-center justify-center bg-[#05080C] text-white">
                <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                    <p className="text-lg">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    const totalVulns = scanStats.vulnerabilities.critical + scanStats.vulnerabilities.high +
        scanStats.vulnerabilities.medium + scanStats.vulnerabilities.low;

    // calculate health score based on vulnerabilities
    const getHealthScore = () => {
        if (totalVulns === 0) return { grade: 'A+', label: 'EXCELLENT', color: 'green' };
        const criticalWeight = scanStats.vulnerabilities.critical * 10;
        const highWeight = scanStats.vulnerabilities.high * 5;
        const mediumWeight = scanStats.vulnerabilities.medium * 2;
        const lowWeight = scanStats.vulnerabilities.low * 1;
        const score = 100 - Math.min(criticalWeight + highWeight + mediumWeight + lowWeight, 100);

        if (score >= 90) return { grade: 'A', label: 'EXCELLENT', color: 'green' };
        if (score >= 80) return { grade: 'B+', label: 'GOOD', color: 'green' };
        if (score >= 70) return { grade: 'B', label: 'FAIR', color: 'yellow' };
        if (score >= 60) return { grade: 'C', label: 'NEEDS WORK', color: 'orange' };
        return { grade: 'D', label: 'CRITICAL', color: 'red' };
    };

    const healthScore = getHealthScore();
    const healthColorClasses = {
        green: 'text-green-400 bg-green-500/10 border-green-500/20',
        yellow: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
        orange: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
        red: 'text-red-400 bg-red-500/10 border-red-500/20'
    };

    return (
        <>
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">Organization Dashboard</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        Overview of your organization security posture.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* vulnerability breakdown */}
                <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                    <h3 className="text-lg font-semibold text-white">Vulnerabilities by Severity</h3>
                    <div className="flex-1 flex flex-col justify-center items-center gap-4">
                        <div className="relative w-40 h-40">
                            <svg className="w-full h-full" viewBox="0 0 36 36">
                                <path className="stroke-current text-gray-800" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" strokeWidth="3"></path>
                                <path className="stroke-current text-red-500" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831" fill="none" strokeDasharray={`${totalVulns > 0 ? Math.min((scanStats.vulnerabilities.critical / totalVulns) * 100, 100) : 0}, 100`} strokeWidth="3"></path>
                            </svg>
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="text-3xl font-bold text-white">{totalVulns}</span>
                                <span className="text-sm text-gray-500">Total</span>
                            </div>
                        </div>
                        <div className="w-full grid grid-cols-2 gap-x-4 gap-y-2 text-sm text-gray-300">
                            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-red-500"></span><span>Critical</span><span className="ml-auto font-medium">{scanStats.vulnerabilities.critical}</span></div>
                            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-orange-500"></span><span>High</span><span className="ml-auto font-medium">{scanStats.vulnerabilities.high}</span></div>
                            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-yellow-500"></span><span>Medium</span><span className="ml-auto font-medium">{scanStats.vulnerabilities.medium}</span></div>
                            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-blue-500"></span><span>Low</span><span className="ml-auto font-medium">{scanStats.vulnerabilities.low}</span></div>
                        </div>
                    </div>
                </div>

                {/* security health score */}
                <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                    <h3 className="text-lg font-semibold text-white">Security Health Score</h3>
                    <div className="flex-1 flex flex-col justify-center items-center">
                        <div className={`relative size-32 rounded-full flex items-center justify-center border-4 ${healthColorClasses[healthScore.color]}`}>
                            <div className="flex flex-col items-center">
                                <span className={`text-4xl font-extrabold ${healthColorClasses[healthScore.color].split(' ')[0]}`}>{healthScore.grade}</span>
                                <span className={`text-xs font-semibold mt-1 ${healthColorClasses[healthScore.color].split(' ')[0]}`}>{healthScore.label}</span>
                            </div>
                        </div>
                        <div className="mt-6 text-center space-y-1">
                            <p className="text-sm font-medium text-white">{totalVulns === 0 ? 'No vulnerabilities detected' : `${totalVulns} open vulnerabilities`}</p>
                            <p className="text-xs text-gray-500">Based on {scanStats.completedScans} completed scans</p>
                        </div>
                    </div>
                </div>

                {/* scan statistics */}
                <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                    <h3 className="text-lg font-semibold text-white">Scan Overview</h3>
                    <div className="flex-1 flex flex-col justify-center space-y-6">
                        <div className="flex items-center gap-4">
                            <div className="relative size-16 shrink-0">
                                <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                                    <circle className="stroke-current text-gray-800" cx="18" cy="18" fill="none" r="15.9155" strokeWidth="4"></circle>
                                    <circle className="stroke-current text-[#136dec]" cx="18" cy="18" fill="none" r="15.9155" strokeDasharray={`${repositories.length > 0 ? (repositories.filter(r => r.last_scanned_commit).length / repositories.length) * 100 : 0}, 100`} strokeWidth="4" strokeLinecap="round"></circle>
                                </svg>
                                <div className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white">
                                    {repositories.length > 0 ? Math.round((repositories.filter(r => r.last_scanned_commit).length / repositories.length) * 100) : 0}%
                                </div>
                            </div>
                            <div>
                                <p className="font-bold text-white">Repositories Scanned</p>
                                <p className="text-xs text-gray-500">{repositories.filter(r => r.last_scanned_commit).length} of {repositories.length} repos have been scanned</p>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <div>
                                <div className="flex justify-between text-xs mb-1 text-gray-300">
                                    <span>Total Scans</span>
                                    <span className="font-semibold">{scanStats.totalScans}</span>
                                </div>
                                <div className="w-full bg-gray-800 rounded-full h-1.5">
                                    <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: '100%' }}></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-xs mb-1 text-gray-300">
                                    <span>Completed Scans</span>
                                    <span className="font-semibold">{scanStats.completedScans}</span>
                                </div>
                                <div className="w-full bg-gray-800 rounded-full h-1.5">
                                    <div className="bg-green-500 h-1.5 rounded-full" style={{ width: scanStats.totalScans > 0 ? `${(scanStats.completedScans / scanStats.totalScans) * 100}%` : '0%' }}></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* connected repositories summary */}
            <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                <div className="flex flex-wrap justify-between items-center gap-2">
                    <h3 className="text-lg font-semibold text-white">Connected Repositories ({repositories.length})</h3>
                    <button onClick={() => navigate('/tenant-dashboard/repositories')} className="text-sm text-primary hover:underline font-medium">View All</button>
                </div>
                <div className="overflow-x-auto -mx-6">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-white/5 border-b border-white/10">
                            <tr className="text-sm text-gray-400 border-b border-white/10">
                                <th className="py-3 px-6 font-medium">Repository</th>
                                <th className="py-3 px-6 font-medium">Scan Status</th>
                                <th className="py-3 px-6 font-medium text-right">Last Scanned</th>
                            </tr>
                        </thead>
                        <tbody>
                            {repositories.slice(0, 5).map(repo => (
                                <tr key={repo.id} className="text-sm border-b border-white/5 text-gray-300 hover:bg-white/5 transition-colors">
                                    <td className="py-4 px-6 font-medium text-white">
                                        <div className="flex flex-col">
                                            <span className="font-semibold text-base">{repo.name}</span>
                                            <span className="text-xs text-blue-400 truncate max-w-xs">{repo.url}</span>
                                        </div>
                                    </td>
                                    <td className="py-4 px-6">
                                        {repo.last_scanned_commit ? (
                                            <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-semibold bg-green-500/10 text-green-400 border border-green-500/20">
                                                <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                                                Scanned
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-semibold bg-gray-500/10 text-gray-400 border border-gray-500/20">
                                                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                                                Not scanned
                                            </span>
                                        )}
                                    </td>
                                    <td className="py-4 px-6 text-right">
                                        <span className="text-xs text-gray-500">
                                            {repo.last_scanned_at ? new Date(repo.last_scanned_at).toLocaleDateString() : '-'}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                            {repositories.length === 0 && <tr><td colSpan="3" className="py-4 px-6 text-center text-gray-500">No repositories connected.</td></tr>}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Team Members Summary */}
            <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                <div className="flex flex-wrap justify-between items-center gap-4">
                    <div>
                        <h3 className="text-lg font-semibold text-white">Team Members</h3>
                        <p className="text-sm text-gray-400">Recent active members.</p>
                    </div>
                    <button onClick={() => navigate('/tenant-dashboard/developers')} className="text-sm text-primary hover:underline font-medium">View All</button>
                </div>
                <div className="overflow-x-auto -mx-6">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-white/5 border-b border-white/10">
                            <tr className="text-sm text-gray-400 border-b border-white/10">
                                <th className="py-3 px-6 font-medium">Developer</th>
                                <th className="py-3 px-6 font-medium">Role</th>
                                <th className="py-3 px-6 font-medium text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {members.slice(0, 5).map(member => (
                                <tr key={member.id} className="text-sm border-b border-white/5 text-gray-300 hover:bg-white/5 transition-colors">
                                    <td className="py-4 px-6 font-medium text-white">
                                        <div className="flex items-center gap-3">
                                            <div className="bg-primary/20 rounded-full size-8 flex items-center justify-center text-primary font-bold">
                                                {member.first_name?.[0] || 'U'}
                                            </div>
                                            <div>
                                                <p>{member.first_name} {member.last_name}</p>
                                                <p className="text-xs text-gray-500">{member.email}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="py-4 px-6">
                                        <span className="badge badge-ghost text-xs bg-white/5 text-gray-300 border-white/10">{member.role}</span>
                                    </td>
                                    <td className="py-4 px-6 text-right">
                                        <span className="text-xs text-green-400 font-medium">Active</span>
                                    </td>
                                </tr>
                            ))}
                            {members.length === 0 && <tr><td colSpan="3" className="py-8 text-center text-gray-500">No members found.</td></tr>}
                        </tbody>
                    </table>
                </div>
            </div>
        </>
    );
};

export default Dashboard;


