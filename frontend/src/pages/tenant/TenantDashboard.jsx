import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useSearchParams } from 'react-router-dom';
import TenantSidebar from '../../components/tenant/TenantSidebar';
import CredentialsPage from './CredentialsPage';
import { Search, Bell, HelpCircle, Plus, Github, Link as LinkIcon, Trash2, Edit, X, Save, Mail, UserPlus, Menu } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';
import Swal from 'sweetalert2';

const TenantDashboard = () => {
    const { user, tenant, logout } = useAuth();
    const [activeTab, setActiveTab] = useState('dashboard');
    const [currentTenant, setCurrentTenant] = useState(null);
    const [sidebarOpen, setSidebarOpen] = useState(false); // Mobile Sidebar State

    // Data States
    const [members, setMembers] = useState([]);
    const [repositories, setRepositories] = useState([]);
    const [invites, setInvites] = useState([]);

    // Profile Edit State
    const [isEditingProfile, setIsEditingProfile] = useState(false);
    const [tenantName, setTenantName] = useState('');
    const [tenantDescription, setTenantDescription] = useState('');

    // Modals State
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [inviteEmail, setInviteEmail] = useState('');
    const [isInviting, setIsInviting] = useState(false);
    const [showRepoModal, setShowRepoModal] = useState(false);
    const [repoData, setRepoData] = useState({ name: '', url: '', visibility: 'private' });
    const [showAssignModal, setShowAssignModal] = useState(false);
    const [selectedRepo, setSelectedRepo] = useState(null);
    const [selectedDevs, setSelectedDevs] = useState([]);
    const [resendingInvite, setResendingInvite] = useState(null);

    const [searchParams] = useSearchParams();

    useEffect(() => {
        if (tenant) {
            setCurrentTenant(tenant);
            setTenantName(tenant?.name || '');
            setTenantDescription(tenant?.description || '');
        }
    }, [tenant]);

    // Handle GitHub OAuth success
    useEffect(() => {
        const githubConnected = searchParams.get('github_connected');
        const credentialId = searchParams.get('credential_id');
        
        if (githubConnected === 'true') {
            toast.success('GitHub connected successfully! You can now manage your repositories.');
            setActiveTab('credentials'); // Switch to credentials tab
            // Clean up URL parameters
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }, [searchParams]);

    // Fetch members and repositories once when tenant is set
    useEffect(() => {
        if (currentTenant) {
            fetchMembers();
            fetchRepositories();
        }
    }, [currentTenant]);

    // Fetch invites only when on developers tab
    useEffect(() => {
        if (currentTenant && activeTab === 'developers') {
            fetchInvites();
        }
    }, [currentTenant, activeTab]);

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

    const fetchInvites = async () => {
        if (!currentTenant) return;
        try {
            const res = await api.get(`/tenants/${currentTenant.id}/invites/`);
            setInvites(res.data.invites || []);
        } catch (error) {
            console.error("Failed to fetch invites", error);
        }
    };

    // --- Action Handlers (Kept from original) ---
    const handleUpdateProfile = async (e) => {
        e.preventDefault();
        try {
            const res = await api.put(`/tenants/${currentTenant.id}/update/`, { name: tenantName, description: tenantDescription });
            if (res.data.success) {
                toast.success("Tenant profile updated");
                setIsEditingProfile(false);
                setCurrentTenant({ ...currentTenant, name: tenantName, description: tenantDescription });
            }
        } catch (error) {
            toast.error("Failed to update profile");
        }
    };

    const handleInvite = async (e) => {
        e.preventDefault();
        setIsInviting(true);
        try {
            const res = await api.post(`/tenants/${currentTenant.id}/invite/`, { email: inviteEmail });
            if (res.data.success) {
                toast.success(`Invitation sent to ${inviteEmail}`);
                setInviteEmail('');
                setShowInviteModal(false);
                fetchInvites();
            }
        } catch (error) {
            toast.error(error.response?.data?.error?.message || "Failed to send invite");
        } finally {
            setIsInviting(false);
        }
    };

    const handleResendInvite = async (inviteId) => {
        setResendingInvite(inviteId);
        try {
            const res = await api.post(`/tenants/${currentTenant.id}/invites/${inviteId}/resend/`);
            if (res.data.success) {
                toast.success(res.data.message);
                fetchInvites();
            }
        } catch (error) {
            toast.error(error.response?.data?.error?.message || "Failed to resend invite");
        } finally {
            setResendingInvite(null);
        }
    };

    const handleCancelInvite = async (inviteId) => {
        const isConfirmed = await showConfirmDialog({
            title: 'Cancel Invite?',
            text: "This invitation will be cancelled.",
            icon: 'warning'
        });
        if (!isConfirmed) return;

        try {
            const res = await api.delete(`/tenants/${currentTenant.id}/invites/${inviteId}/cancel/`);
            if (res.data.success) {
                showSuccessToast("Invitation cancelled");
                fetchInvites();
            }
        } catch (error) {
            showErrorToast("Failed to cancel invite");
        }
    };

    const handleRemoveMember = async (id) => {
        const isConfirmed = await showConfirmDialog({ title: 'Remove Member?', text: "They will lose access.", icon: 'warning' });
        if (!isConfirmed) return;
        try {
            const res = await api.delete(`/tenants/${currentTenant.id}/members/${id}/remove/`);
            if (res.data.success) {
                showSuccessToast("Member removed");
                setMembers(members.filter(m => m.id !== id));
            }
        } catch (error) {
            showErrorToast("Failed to remove member");
        }
    };

    const handleAddRepo = async (e) => {
        e.preventDefault();
        try {
            await api.post(`/tenants/${currentTenant.id}/repositories/create/`, repoData);
            toast.success("Repository added successfully");
            setShowRepoModal(false);
            setRepoData({ name: '', url: '', visibility: 'private' });
            fetchRepositories();
        } catch (error) {
            toast.error("Failed to add repository");
        }
    };

    const handleAssignDevs = async () => {
        try {
            await api.patch(`/tenants/${currentTenant.id}/repositories/${selectedRepo.id}/`, { assigned_developers: selectedDevs });
            toast.success("Developers assigned successfully");
            setShowAssignModal(false);
            fetchRepositories();
        } catch (error) {
            toast.error("Failed to assign developers");
        }
    };

    if (!currentTenant) {
        return (
            <div className="h-screen flex flex-col items-center justify-center bg-[#05080C] text-white">
                <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                    <p className="text-lg">Loading tenant data...</p>
                    {!tenant && (
                        <p className="text-sm text-gray-400">
                            No tenant found. You may need to be invited to a tenant first.
                        </p>
                    )}
                </div>
            </div>
        );
    }

    // --- Render Helpers ---

    return (
        <div className="flex h-screen w-full bg-[#05080C] text-white font-sans overflow-hidden">

            {/* Sidebar Component */}
            <TenantSidebar
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                logout={logout}
                user={user}
                tenantName={currentTenant.name}
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
            />

            {/* Main Content Area */}
            <div className="flex flex-1 flex-col overflow-y-auto relative w-full">

                {/* Header */}
                <header className="flex sticky top-0 z-10 items-center justify-between whitespace-nowrap border-b border-white/10 px-6 py-3 bg-[#05080C]/80 backdrop-blur-sm">
                    <div className="flex items-center gap-4 lg:gap-8">
                        {/* Mobile Toggle Button */}
                        <button
                            className="lg:hidden p-2 -ml-2 text-gray-400 hover:text-white"
                            onClick={() => setSidebarOpen(true)}
                        >
                            <Menu className="w-6 h-6" />
                        </button>

                        <div className="flex items-center gap-3">
                            <h2 className="text-lg font-bold leading-tight text-white">SecuredHub</h2>
                        </div>
                        <label className="hidden md:flex flex-col min-w-40 !h-10 max-w-64">
                            <div className="flex w-full flex-1 items-stretch rounded-lg h-full bg-[#0A0F16] border border-white/10">
                                <div className="text-gray-400 flex items-center justify-center pl-3">
                                    <Search className="w-5 h-5" />
                                </div>
                                <input className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg bg-transparent h-full placeholder:text-gray-500 pl-2 text-base outline-none border-none text-white" placeholder="Search" />
                            </div>
                        </label>
                    </div>
                    <div className="flex flex-1 justify-end gap-3 lg:gap-4 items-center">
                        <button className="hidden sm:flex cursor-pointer items-center justify-center rounded-full h-10 w-10 text-gray-400 hover:bg-white/10 hover:text-white transition-colors">
                            <Bell className="w-5 h-5" />
                        </button>
                        <button className="hidden sm:flex cursor-pointer items-center justify-center rounded-full h-10 w-10 text-gray-400 hover:bg-white/10 hover:text-white transition-colors">
                            <HelpCircle className="w-5 h-5" />
                        </button>
                        <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 bg-primary/20 flex items-center justify-center text-primary font-bold">
                            {user?.first_name?.[0]}
                        </div>
                    </div>
                </header>

                <main className="flex-1 p-4 lg:p-8">
                    <div className="max-w-7xl mx-auto space-y-6 lg:space-y-8">

                        {/* Title Section (Dynamic based on tab) */}
                        <div className="flex flex-wrap justify-between items-center gap-4">
                            <div className="flex min-w-72 flex-col gap-1">
                                <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">
                                    {activeTab === 'dashboard' ? 'Organization Dashboard' :
                                        activeTab === 'repositories' ? 'Repositories' :
                                            activeTab === 'developers' ? 'Team Management' :
                                                activeTab === 'profile' ? 'Organization Profile' :
                                                    activeTab === 'credentials' ? 'Repository Credentials' :
                                                        activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
                                </p>
                                <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                                    {activeTab === 'dashboard' ? 'Overview of your organization security posture.' :
                                        activeTab === 'repositories' ? 'Manage and connect your code repositories.' :
                                            activeTab === 'developers' ? 'Manage access and roles for your organization.' :
                                                activeTab === 'profile' ? 'Update your organization details.' :
                                                    activeTab === 'credentials' ? 'Manage access tokens for your code repositories.' :
                                                        'Manage your organization settings.'}
                                </p>
                            </div>
                        </div>

                        {/* Action Buttons (Contextual) */}
                        {activeTab === 'repositories' && (
                            <div className="flex flex-wrap gap-3 justify-start">
                                <button onClick={() => setShowRepoModal(true)} className="flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-[#136dec] text-white text-sm font-bold gap-2 hover:bg-blue-600 transition-colors">
                                    <Github className="w-4 h-4" />
                                    <span className="truncate">Add Repository</span>
                                </button>
                            </div>
                        )}
                        {activeTab === 'developers' && (
                            <div className="flex flex-wrap gap-3 justify-start">
                                <button onClick={() => setShowInviteModal(true)} className="flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold gap-2 hover:bg-blue-600 transition-colors">
                                    <UserPlus className="w-4 h-4" />
                                    <span className="truncate">Invite Developer</span>
                                </button>
                            </div>
                        )}

                        {/* DASHBOARD VIEW */}
                        {activeTab === 'dashboard' && (
                            <>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {/* Widget 1: Vulnerabilities */}
                                    <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                                        <h3 className="text-lg font-semibold text-white">Vulnerabilities by Severity</h3>
                                        <div className="flex-1 flex flex-col justify-center items-center gap-4">
                                            {/* Simplified SVG Placeholder */}
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
                                        <button onClick={() => setActiveTab('repositories')} className="text-sm text-primary hover:underline font-medium">View All</button>
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
                                        <button onClick={() => setActiveTab('developers')} className="text-sm text-primary hover:underline font-medium">View All</button>
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
                        )}

                        {/* REPOSITORIES VIEW */}
                        {activeTab === 'repositories' && (
                            <div className="flex flex-col gap-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {repositories.map(repo => (
                                        <div key={repo.id} className="flex flex-col gap-3 p-6 rounded-xl border border-white/10 bg-[#0A0F16]">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <h4 className="font-bold text-lg text-white">{repo.name}</h4>
                                                    <a href={repo.url} target="_blank" rel="noreferrer" className="text-sm text-blue-500 hover:underline flex items-center gap-1">
                                                        <LinkIcon className="w-3 h-3" /> {repo.url}
                                                    </a>
                                                </div>
                                                <span className={`badge ${repo.visibility === 'private' ? 'badge-warning bg-yellow-500/10 text-yellow-400 border-none' : 'badge-success bg-green-500/10 text-green-400 border-none'}`}>{repo.visibility}</span>
                                            </div>
                                            <div className="mt-auto pt-4 border-t border-white/10 flex justify-end items-center">
                                                <button className="btn btn-sm btn-ghost text-primary hover:bg-primary/10" onClick={() => { setSelectedRepo(repo); setShowAssignModal(true); }}>
                                                    Assign Developers
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                    {repositories.length === 0 && <div className="col-span-full text-center py-10 text-gray-500">No repositories connected. Add one to get started.</div>}
                                </div>
                            </div>
                        )}

                        {/* DEVELOPERS VIEW */}
                        {activeTab === 'developers' && (
                            <div className="flex flex-col gap-6">
                                {/* Active Members */}
                                <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                                    <h3 className="text-lg font-semibold text-white">Active Members</h3>
                                    <div className="overflow-x-auto -mx-6">
                                        <table className="w-full text-left border-collapse">
                                            <thead className="bg-white/5 border-b border-white/10">
                                                <tr className="text-sm text-gray-400 border-b border-white/10">
                                                    <th className="py-2 px-6 font-medium">Name</th>
                                                    <th className="py-2 px-6 font-medium">Email</th>
                                                    <th className="py-2 px-6 font-medium">Role</th>
                                                    <th className="py-2 px-6 font-medium">Joined</th>
                                                    <th className="py-2 px-6 font-medium text-right">Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {members.map(member => (
                                                    <tr key={member.id} className="text-sm border-b border-white/5 text-gray-300 hover:bg-white/5 transition-colors">
                                                        <td className="py-4 px-6 font-medium text-white">
                                                            <div className="flex items-center gap-3">
                                                                <div className="bg-primary/10 rounded-full size-8 flex items-center justify-center text-primary font-bold">
                                                                    {member.first_name?.[0] || 'U'}
                                                                </div>
                                                                <span>{member.first_name} {member.last_name}</span>
                                                            </div>
                                                        </td>
                                                        <td className="py-4 px-6 text-gray-400">{member.email}</td>
                                                        <td className="py-4 px-6">
                                                            <span className={`px-2 py-1 rounded text-xs font-semibold ${member.role === 'owner' ? 'bg-purple-100 text-purple-800 dark:bg-purple-500/20 dark:text-purple-300' : 'bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-300'}`}>
                                                                {member.role.toUpperCase()}
                                                            </span>
                                                        </td>
                                                        <td className="py-4 px-6 text-gray-400">{new Date(member.joined_at).toLocaleDateString()}</td>
                                                        <td className="py-4 px-6 text-right">
                                                            {member.role !== 'owner' && (
                                                                <button onClick={() => handleRemoveMember(member.id)} className="text-red-500 hover:bg-red-500/10 p-2 rounded transition-colors" title="Remove Member">
                                                                    <Trash2 className="w-4 h-4" />
                                                                </button>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                                {members.length === 0 && <tr><td colSpan="5" className="py-8 text-center text-gray-500">No members found.</td></tr>}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                {/* Pending Invites */}
                                {invites.length > 0 && (
                                    <div className="flex flex-col gap-4 rounded-xl p-6 border border-white/10 bg-[#0A0F16]">
                                        <div className="flex items-center gap-2">
                                            <h3 className="text-lg font-semibold text-white">Pending Invitations</h3>
                                            <span className="badge badge-sm bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 border-none">{invites.length}</span>
                                        </div>
                                        <div className="overflow-x-auto -mx-6">
                                            <table className="w-full text-left border-collapse">
                                                <thead className="bg-white/5 border-b border-white/10">
                                                    <tr className="text-sm text-gray-400 border-b border-white/10">
                                                        <th className="py-2 px-6 font-medium">Email</th>
                                                        <th className="py-2 px-6 font-medium">Status</th>
                                                        <th className="py-2 px-6 font-medium">Sent</th>
                                                        <th className="py-2 px-6 font-medium">Expires</th>
                                                        <th className="py-2 px-6 font-medium text-right">Actions</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {invites.map(invite => {
                                                        const isExpired = invite.is_expired || new Date(invite.expires_at) < new Date();
                                                        return (
                                                            <tr key={invite.token} className="text-sm border-b border-white/5 text-gray-300 hover:bg-white/5 transition-colors">
                                                                <td className="py-4 px-6 font-medium text-white">
                                                                    <div className="flex items-center gap-3">
                                                                        <div className="bg-gray-200 dark:bg-gray-700 rounded-full size-8 flex items-center justify-center text-gray-600 dark:text-gray-300">
                                                                            <Mail className="w-4 h-4" />
                                                                        </div>
                                                                        <span>{invite.email}</span>
                                                                    </div>
                                                                </td>
                                                                <td className="py-4 px-6">
                                                                    <span className={`px-2 py-1 rounded text-xs font-semibold ${isExpired
                                                                            ? 'bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-300'
                                                                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-500/20 dark:text-yellow-300'
                                                                        }`}>
                                                                        {isExpired ? 'EXPIRED' : 'PENDING'}
                                                                    </span>
                                                                </td>
                                                                <td className="py-4 px-6 text-gray-400">
                                                                    {new Date(invite.created_at).toLocaleDateString()}
                                                                </td>
                                                                <td className="py-4 px-6 text-gray-400">
                                                                    {new Date(invite.expires_at).toLocaleDateString()}
                                                                </td>
                                                                <td className="py-4 px-6 text-right">
                                                                    <div className="flex items-center justify-end gap-2">
                                                                        {isExpired ? (
                                                                            <button
                                                                                onClick={() => handleResendInvite(invite.token)}
                                                                                className="text-blue-500 hover:bg-blue-500/10 px-3 py-1.5 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium flex items-center gap-1"
                                                                                title="Resend with new token"
                                                                                disabled={resendingInvite === invite.token}
                                                                            >
                                                                                {resendingInvite === invite.token ? (
                                                                                    <>
                                                                                        <span className="loading loading-spinner loading-xs"></span>
                                                                                        <span>Resending...</span>
                                                                                    </>
                                                                                ) : (
                                                                                    <>
                                                                                        <Mail className="w-4 h-4" />
                                                                                        <span>Resend</span>
                                                                                    </>
                                                                                )}
                                                                            </button>
                                                                        ) : (
                                                                            <span className="text-xs text-gray-500 dark:text-gray-400 italic">Waiting for acceptance</span>
                                                                        )}
                                                                        <button
                                                                            onClick={() => handleCancelInvite(invite.token)}
                                                                            className="text-red-500 hover:bg-red-500/10 p-2 rounded transition-colors"
                                                                            title="Cancel invitation"
                                                                        >
                                                                            <X className="w-4 h-4" />
                                                                        </button>
                                                                    </div>
                                                                </td>
                                                            </tr>
                                                        );
                                                    })}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* PROFILE VIEW */}
                        {activeTab === 'profile' && (
                            <div className="card bg-white dark:bg-[#1a1d21] border border-[#e5e7eb] dark:border-[#282f39] shadow-sm max-w-2xl">
                                <div className="card-body">
                                    <div className="flex justify-between items-center mb-6">
                                        <h2 className="card-title">Tenant Profile</h2>
                                        {!isEditingProfile ? (
                                            <button className="btn btn-sm btn-ghost" onClick={() => setIsEditingProfile(true)}>
                                                <Edit className="w-4 h-4 mr-2" /> Edit
                                            </button>
                                        ) : (
                                            <button className="btn btn-sm btn-ghost text-error" onClick={() => setIsEditingProfile(false)}>
                                                <X className="w-4 h-4 mr-2" /> Cancel
                                            </button>
                                        )}
                                    </div>

                                    {isEditingProfile ? (
                                        <form onSubmit={handleUpdateProfile} className="space-y-4">
                                            <div className="form-control">
                                                <label className="label">Name</label>
                                                <input type="text" className="input input-bordered dark:bg-[#101822] dark:border-[#282f39]" value={tenantName} onChange={e => setTenantName(e.target.value)} />
                                            </div>
                                            <div className="form-control">
                                                <label className="label">Description</label>
                                                <textarea className="textarea textarea-bordered dark:bg-[#101822] dark:border-[#282f39]" value={tenantDescription} onChange={e => setTenantDescription(e.target.value)}></textarea>
                                            </div>
                                            <button type="submit" className="btn btn-primary"><Save className="w-4 h-4 mr-2" /> Save Changes</button>
                                        </form>
                                    ) : (
                                        <div className="space-y-6">
                                            <div>
                                                <h3 className="font-bold text-gray-500 text-xs uppercase tracking-wider mb-1">Organization Name</h3>
                                                <p className="text-lg font-medium">{currentTenant.name}</p>
                                            </div>
                                            <div>
                                                <h3 className="font-bold text-gray-500 text-xs uppercase tracking-wider mb-1">Description</h3>
                                                <p className="text-gray-700 dark:text-[#9da8b9]">{currentTenant.description || "No description provided."}</p>
                                            </div>
                                            <div className="divider"></div>
                                            <div>
                                                <h3 className="font-bold text-gray-500 text-xs uppercase tracking-wider mb-1">Primary Owner</h3>
                                                <div className="flex items-center gap-3 mt-2">
                                                    <div className="bg-primary/20 rounded-full size-10 flex items-center justify-center text-primary font-bold">
                                                        {user?.first_name?.[0]}
                                                    </div>
                                                    <div>
                                                        <p className="font-medium">{user.first_name} {user.last_name}</p>
                                                        <p className="text-sm text-gray-500">{user.email}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* CREDENTIALS VIEW */}
                        {activeTab === 'credentials' && (
                            <CredentialsPage />
                        )}

                        {/* PLACEHOLDER VIEWS */}
                        {(activeTab === 'scans' || activeTab === 'reports' || activeTab === 'settings') && (
                            <div className="flex flex-col items-center justify-center h-96 bg-white dark:bg-[#1a1d21] border border-[#e5e7eb] dark:border-[#282f39] rounded-xl text-center p-8">
                                <div className="bg-gray-100 dark:bg-white/5 p-4 rounded-full mb-4">
                                    {activeTab === 'scans' && <Search className="w-12 h-12 text-gray-400" />}
                                    {activeTab === 'reports' && <LinkIcon className="w-12 h-12 text-gray-400" />}
                                    {activeTab === 'settings' && <Edit className="w-12 h-12 text-gray-400" />}
                                </div>
                                <h3 className="text-xl font-bold mb-2">
                                    {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Module
                                </h3>
                                <p className="text-gray-500 max-w-md">
                                    This feature is currently under development. Please check back later for updates on {activeTab} functionality.
                                </p>
                            </div>
                        )}

                    </div>
                </main>
            </div>

            {/* --- MODALS (Unchanged functionality, just updated classes if needed) --- */}
            {showInviteModal && (
                <div className="modal modal-open">
                    <div className="modal-box dark:bg-[#1a1d21] border dark:border-[#282f39]">
                        <h3 className="font-bold text-lg mb-4">Invite Developer</h3>
                        <form onSubmit={handleInvite}>
                            <div className="form-control mb-4">
                                <label className="label">
                                    <span className="label-text">Email Address</span>
                                </label>
                                <input
                                    type="email"
                                    placeholder="developer@example.com"
                                    className="input input-bordered w-full dark:bg-[#101822] dark:border-[#282f39]"
                                    value={inviteEmail}
                                    onChange={e => setInviteEmail(e.target.value)}
                                    disabled={isInviting}
                                    required
                                />
                                <label className="label">
                                    <span className="label-text-alt text-gray-500">An invitation email will be sent to this address</span>
                                </label>
                            </div>
                            <div className="modal-action">
                                <button
                                    type="button"
                                    className="btn btn-ghost"
                                    onClick={() => setShowInviteModal(false)}
                                    disabled={isInviting}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="btn btn-primary bg-primary border-none"
                                    disabled={isInviting}
                                >
                                    {isInviting ? (
                                        <>
                                            <span className="loading loading-spinner loading-sm"></span>
                                            Sending...
                                        </>
                                    ) : (
                                        <>
                                            <Mail className="w-4 h-4" />
                                            Send Invite
                                        </>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {showRepoModal && (
                <div className="modal modal-open">
                    <div className="modal-box dark:bg-[#1a1d21] border dark:border-[#282f39]">
                        <h3 className="font-bold text-lg mb-4">Connect Repository</h3>
                        <form onSubmit={handleAddRepo} className="flex flex-col gap-4">
                            <input type="text" placeholder="Repository Name" className="input input-bordered dark:bg-[#101822] dark:border-[#282f39]" value={repoData.name} onChange={e => setRepoData({ ...repoData, name: e.target.value })} required />
                            <input type="url" placeholder="Repository URL (HTTPS)" className="input input-bordered dark:bg-[#101822] dark:border-[#282f39]" value={repoData.url} onChange={e => setRepoData({ ...repoData, url: e.target.value })} required />
                            <select className="select select-bordered dark:bg-[#101822] dark:border-[#282f39]" value={repoData.visibility} onChange={e => setRepoData({ ...repoData, visibility: e.target.value })}>
                                <option value="private">Private</option>
                                <option value="public">Public</option>
                            </select>
                            <div className="modal-action">
                                <button type="button" className="btn btn-ghost" onClick={() => setShowRepoModal(false)}>Cancel</button>
                                <button type="button" className="btn btn-primary bg-primary border-none">Connect</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {showAssignModal && (
                <div className="modal modal-open">
                    <div className="modal-box dark:bg-[#1a1d21] border dark:border-[#282f39]">
                        <h3 className="font-bold text-lg mb-4">Assign Developers</h3>
                        <div className="flex flex-col gap-2 mb-4">
                            {members.filter(m => m.role === 'developer').map(m => (
                                <label key={m.id} className="label cursor-pointer justify-start gap-4 hover:bg-white/5 p-2 rounded">
                                    <input type="checkbox" className="checkbox checkbox-primary"
                                        checked={selectedDevs.includes(m.user.id)}
                                        onChange={(e) => {
                                            if (e.target.checked) setSelectedDevs([...selectedDevs, m.user.id]);
                                            else setSelectedDevs(selectedDevs.filter(id => id !== m.user.id));
                                        }}
                                    />
                                    <span>{m.user.first_name} {m.user.last_name}</span>
                                </label>
                            ))}
                        </div>
                        <div className="modal-action">
                            <button type="button" className="btn btn-ghost" onClick={() => setShowAssignModal(false)}>Cancel</button>
                            <button type="button" className="btn btn-primary bg-primary border-none" onClick={handleAssignDevs}>Save</button>
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
};

export default TenantDashboard;
