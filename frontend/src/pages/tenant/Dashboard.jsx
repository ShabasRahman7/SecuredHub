import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Link as LinkIcon } from 'lucide-react';
import api from '../../api/axios';

const Dashboard = () => {
    const { user, tenant } = useAuth();
    const navigate = useNavigate();
    const [currentTenant, setCurrentTenant] = useState(null);
    const [members, setMembers] = useState([]);
    const [repositories, setRepositories] = useState([]);

    useEffect(() => {
        if (tenant) {
            setCurrentTenant(tenant);
        }
    }, [tenant]);

    useEffect(() => {
        if (currentTenant) {
            fetchMembers();
            fetchRepositories();
        }
    }, [currentTenant]);

    const fetchMembers = async () => {
        if (!currentTenant) return;
        try {
            const res = await api.get(`/tenants/${currentTenant.id}/members/`);
            setMembers(res.data.members || []);
        } catch (error) {
            console.error('Failed to fetch members', error);
        }
    };

    const fetchRepositories = async () => {
        if (!currentTenant) return;
        try {
            const res = await api.get(`/tenants/${currentTenant.id}/repositories/`);
            setRepositories(res.data.repositories || []);
        } catch (error) {
            console.error("Failed to fetch repositories", error);
        }
    };

    if (!currentTenant) {
        return (
            <div className="h-screen flex flex-col items-center justify-center bg-[#05080C] text-white">
                <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                    <p className="text-lg">Loading tenant data...</p>
                </div>
            </div>
        );
    }

    return (
        <>
            {/* Title Section */}
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">Organization Dashboard</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        Overview of your organization security posture.
                    </p>
                </div>
            </div>

            {/* Dashboard Content */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Widget 1: Vulnerabilities */}
                <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                    <h3 className="text-lg font-semibold text-white">Vulnerabilities by Severity</h3>
                    <div className="flex-1 flex flex-col justify-center items-center gap-4">
                        <div className="relative w-40 h-40">
                            <svg className="w-full h-full" viewBox="0 0 36 36">
                                <path className="stroke-current text-gray-800" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" strokeWidth="3"></path>
                                <path className="stroke-current text-red-500" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831" fill="none" strokeDasharray="25, 100" strokeWidth="3"></path>
                            </svg>
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="text-3xl font-bold text-white">86</span>
                                <span className="text-sm text-gray-500">Open</span>
                            </div>
                        </div>
                        <div className="w-full grid grid-cols-2 gap-x-4 gap-y-2 text-sm text-gray-300">
                            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-red-500"></span><span>Critical</span><span className="ml-auto font-medium">21</span></div>
                            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-orange-500"></span><span>High</span><span className="ml-auto font-medium">30</span></div>
                        </div>
                    </div>
                </div>

                {/* Widget 2: Security Health Score */}
                <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                    <h3 className="text-lg font-semibold text-white">Security Health Score</h3>
                    <div className="flex-1 flex flex-col justify-center items-center">
                        <div className="relative size-32 bg-green-500/10 rounded-full flex items-center justify-center border-4 border-green-500/20">
                            <div className="flex flex-col items-center">
                                <span className="text-4xl font-extrabold text-green-400">B+</span>
                                <span className="text-xs font-semibold text-green-400 mt-1">GOOD</span>
                            </div>
                            <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 36 36">
                                <path className="stroke-current text-green-500" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" strokeDasharray="75, 100" strokeWidth="2" strokeLinecap="round"></path>
                            </svg>
                        </div>
                        <div className="mt-6 text-center space-y-1">
                            <p className="text-sm font-medium text-white">Passing standard checks</p>
                            <p className="text-xs text-gray-500">Score based on open vulnerabilities and resolution time.</p>
                        </div>
                    </div>
                </div>

                {/* Widget 3: AI Analysis Coverage */}
                <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                    <h3 className="text-lg font-semibold text-white">AI Analysis Coverage</h3>
                    <div className="flex-1 flex flex-col justify-center space-y-6">
                        <div className="flex items-center gap-4">
                            <div className="relative size-16 shrink-0">
                                <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                                    <circle className="stroke-current text-gray-800" cx="18" cy="18" fill="none" r="15.9155" strokeWidth="4"></circle>
                                    <circle className="stroke-current text-[#136dec]" cx="18" cy="18" fill="none" r="15.9155" strokeDasharray="90, 100" strokeWidth="4" strokeLinecap="round"></circle>
                                </svg>
                                <div className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white">90%</div>
                            </div>
                            <div>
                                <p className="font-bold text-white">Codebase Scanned</p>
                                <p className="text-xs text-gray-500">The AI has processed most of your connected repositories.</p>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <div>
                                <div className="flex justify-between text-xs mb-1 text-gray-300">
                                    <span>Auto-Remediation</span>
                                    <span className="font-semibold">77%</span>
                                </div>
                                <div className="w-full bg-gray-800 rounded-full h-1.5">
                                    <div className="bg-purple-500 h-1.5 rounded-full" style={{ width: '77%' }}></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-xs mb-1 text-gray-300">
                                    <span>False Positives Filtered</span>
                                    <span className="font-semibold">92%</span>
                                </div>
                                <div className="w-full bg-gray-800 rounded-full h-1.5">
                                    <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: '92%' }}></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Connected Repositories Summary */}
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
                                <th className="py-3 px-6 font-medium">Visibility</th>
                                <th className="py-3 px-6 font-medium text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {repositories.slice(0, 5).map(repo => (
                                <tr key={repo.id} className="text-sm border-b border-white/5 text-gray-300 hover:bg-white/5 transition-colors">
                                    <td className="py-4 px-6 font-medium text-white">
                                        <div className="flex flex-col">
                                            <span className="font-semibold text-base">{repo.name}</span>
                                            <span className="text-xs text-blue-400">{repo.url}</span>
                                        </div>
                                    </td>
                                    <td className="py-4 px-6">
                                        <span className={`px-2 py-1 rounded text-xs font-semibold ${repo.visibility === 'private' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' : 'bg-green-500/10 text-green-400 border border-green-500/20'}`}>
                                            {repo.visibility}
                                        </span>
                                    </td>
                                    <td className="py-4 px-6 text-right">
                                        <span className="text-xs text-gray-500">Connected</span>
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

