import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Link as LinkIcon, Trash2, Github, Search, X, Users, UserPlus, UserMinus } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';
import { showConfirmDialog, showSuccessToast, showErrorToast } from '../../utils/sweetAlert';
import { tenantService } from '../../api/services/tenantService';
import { credentialsApi } from '../../services/credentialsApi';
import { API_ENDPOINTS } from '../../constants/api';

const Repositories = () => {
    const { tenant } = useAuth();
    const [currentTenant, setCurrentTenant] = useState(null);
    const [repositories, setRepositories] = useState([]);
    const [members, setMembers] = useState([]);
    const [assignments, setAssignments] = useState({});
    const [showGitHubModal, setShowGitHubModal] = useState(false);
    const [showRepoModal, setShowRepoModal] = useState(false);
    const [showAssignModal, setShowAssignModal] = useState(false);
    const [selectedRepoForAssign, setSelectedRepoForAssign] = useState(null);
    const [assignSearch, setAssignSearch] = useState('');
    const [assignSelectedMemberIds, setAssignSelectedMemberIds] = useState([]);
    const [assignSaving, setAssignSaving] = useState(false);
    const [ghRepos, setGhRepos] = useState([]);
    const [filteredGhRepos, setFilteredGhRepos] = useState([]);
    const [loadingGhRepos, setLoadingGhRepos] = useState(false);
    const [selectedRepo, setSelectedRepo] = useState(null);
    const [searchRepo, setSearchRepo] = useState('');
    const [repoFormData, setRepoFormData] = useState({ name: '', url: '', visibility: 'private' });

    useEffect(() => {
        if (tenant) {
            setCurrentTenant(tenant);
        }
    }, [tenant]);

    useEffect(() => {
        if (currentTenant) {
            fetchRepositories();
            fetchMembers();
        }
    }, [currentTenant]);

    const fetchRepositories = async () => {
        if (!currentTenant) return;
        try {
            const res = await api.get(API_ENDPOINTS.TENANT_REPOSITORIES(currentTenant.id));
            setRepositories(res.data.repositories || []);
            const assignmentsData = {};
            for (const repo of res.data.repositories || []) {
                try {
                    const assignRes = await api.get(API_ENDPOINTS.REPOSITORY_ASSIGNMENTS(currentTenant.id, repo.id));
                    assignmentsData[repo.id] = assignRes.data.assigned_member_ids || [];
                } catch (err) {
                    assignmentsData[repo.id] = [];
                }
            }
            setAssignments(assignmentsData);
        } catch (error) {
            toast.error('Failed to load repositories');
        }
    };

    const fetchMembers = async () => {
        if (!currentTenant) return;
        try {
            const res = await api.get(API_ENDPOINTS.TENANT_MEMBERS(currentTenant.id));
            const developers = (res.data.members || []).filter(m => m.role === 'developer' && !m.deleted_at);
            setMembers(developers);
        } catch (error) {
            toast.error('Failed to load members');
        }
    };

    const handleAddRepo = async (repoData) => {
        try {
            await api.post(API_ENDPOINTS.ADD_REPOSITORY(currentTenant.id), repoData);
            toast.success("Repository added successfully");
            fetchRepositories();
            return true;
        } catch (error) {
            toast.error("Failed to add repository");
            return false;
        }
    };

    const handleDeleteRepository = async (repoId, repoName) => {
        const isConfirmed = await showConfirmDialog({
            title: 'Delete Repository?',
            text: `This will remove "${repoName}" from your organization. This action cannot be undone.`,
            icon: 'warning'
        });
        if (!isConfirmed) return;

        try {
            await tenantService.deleteRepository(currentTenant.id, repoId);
            showSuccessToast("Repository deleted successfully");
            fetchRepositories();
        } catch (error) {
            showErrorToast("Failed to delete repository");
        }
    };

    const fetchGitHubRepos = async () => {
        try {
            setLoadingGhRepos(true);
            setSelectedRepo(null);
            setSearchRepo('');
            const credsRes = await credentialsApi.listCredentials(currentTenant.id);
            const cred = (credsRes.credentials || []).find(c => c.provider === 'github');

            if (!cred) {
                toast.error('No GitHub credential found. Connect GitHub first.');
                setShowGitHubModal(false);
                return;
            }

            const response = await credentialsApi.getGitHubRepositories(currentTenant.id, cred.id);
            const repos = response.repositories || [];

            const existingUrls = repositories.map(repo => repo.url.toLowerCase());
            const availableRepos = repos.filter(repo => {
                const repoUrl = (repo.clone_url || repo.html_url || '').toLowerCase();
                return !existingUrls.includes(repoUrl);
            });

            setGhRepos(availableRepos);
            setFilteredGhRepos(availableRepos);
        } catch (err) {
            toast.error('Failed to load GitHub repositories');
        } finally {
            setLoadingGhRepos(false);
        }
    };

    const handleSearchRepo = (value) => {
        setSearchRepo(value);
        const q = value.trim().toLowerCase();
        if (!q) {
            setFilteredGhRepos(ghRepos);
            return;
        }
        setFilteredGhRepos(ghRepos.filter(r =>
            (r.name || '').toLowerCase().includes(q) ||
            (r.full_name || '').toLowerCase().includes(q)
        ));
    };

    const handleImportRepo = async () => {
        if (!selectedRepo) {
            toast.error('Select a repository first');
            return;
        }

        try {
            await tenantService.addRepository(currentTenant.id, {
                name: selectedRepo.name,
                url: selectedRepo.clone_url || selectedRepo.html_url,
                visibility: selectedRepo.private ? 'private' : 'public',
            });

            toast.success('Repository imported successfully!');
            fetchRepositories();
            setShowGitHubModal(false);
        } catch (err) {
            toast.error('Failed to import repository');
        }
    };

    const handleAddRepoSubmit = async (e) => {
        e.preventDefault();
        const success = await handleAddRepo(repoFormData);
        if (success) {
            setRepoFormData({ name: '', url: '', visibility: 'private' });
            setShowRepoModal(false);
        }
    };

    useEffect(() => {
        if (showGitHubModal && currentTenant) {
            fetchGitHubRepos();
        }
    }, [showGitHubModal, currentTenant]);

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
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">Repositories</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        Manage and connect your code repositories.
                    </p>
                </div>
            </div>

            <div className="flex flex-wrap gap-3 justify-start">
                <button
                    onClick={() => setShowGitHubModal(true)}
                    className="flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-[#136dec] text-white text-sm font-bold gap-2 hover:bg-blue-600 transition-colors"
                >
                    <Github className="w-4 h-4" />
                    <span>Import from GitHub</span>
                </button>
            </div>

            <div className="bg-[#0A0F16] rounded-xl border border-white/10 overflow-hidden">
                {repositories.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        <Github className="w-12 h-12 mx-auto mb-4 text-gray-600" />
                        <p className="text-lg">No repositories connected</p>
                        <p className="text-sm mt-2">Import from GitHub to get started</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="table w-full">
                            <thead>
                                <tr className="border-b border-white/10">
                                    <th className="text-gray-400 font-semibold">Repository</th>
                                    <th className="text-gray-400 font-semibold">Visibility</th>
                                    <th className="text-gray-400 font-semibold">Assigned Developers</th>
                                    <th className="text-gray-400 font-semibold">Created</th>
                                    <th className="text-gray-400 font-semibold text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {repositories.map(repo => {
                                    const assignedMemberIds = assignments[repo.id] || [];
                                    const assignedMembers = members.filter(m => assignedMemberIds.includes(m.id));
                                    return (
                                        <tr key={repo.id} className="border-b border-white/5 hover:bg-white/5">
                                            <td>
                                                <div>
                                                    <div className="font-semibold text-white">{repo.name}</div>
                                                    <a
                                                        href={repo.url}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        className="text-sm text-blue-400 hover:underline flex items-center gap-1 mt-1"
                                                    >
                                                        <LinkIcon className="w-3 h-3" />
                                                        <span className="truncate max-w-xs">{repo.url}</span>
                                                    </a>
                                                </div>
                                            </td>
                                            <td>
                                                <span className={`badge badge-sm ${repo.visibility === 'private'
                                                    ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                                                    : 'bg-green-500/10 text-green-400 border-green-500/20'
                                                    } border`}>
                                                    {repo.visibility}
                                                </span>
                                            </td>
                                            <td>
                                                <div className="flex items-center gap-2">
                                                    {assignedMembers.length > 0 ? (
                                                        <>
                                                            <Users className="w-4 h-4 text-gray-400" />
                                                            <span className="text-sm text-gray-300">{assignedMembers.length}</span>
                                                            <span className="text-xs text-gray-500">
                                                                ({assignedMembers.map(m => m.email).join(', ')})
                                                            </span>
                                                        </>
                                                    ) : (
                                                        <span className="text-sm text-gray-500">None assigned</span>
                                                    )}
                                                </div>
                                            </td>
                                            <td>
                                                <span className="text-sm text-gray-400">
                                                    {new Date(repo.created_at).toLocaleDateString()}
                                                </span>
                                            </td>
                                            <td>
                                                <div className="flex items-center justify-end gap-2">
                                                    <button
                                                        className="btn btn-sm btn-ghost text-blue-400 hover:bg-blue-500/10"
                                                        onClick={() => {
                                                            setSelectedRepoForAssign(repo);
                                                            const currentAssigned = assignments[repo.id] || [];
                                                            setAssignSelectedMemberIds(currentAssigned);
                                                            setAssignSearch('');
                                                            setShowAssignModal(true);
                                                        }}
                                                        title="Manage Assignments"
                                                    >
                                                        <UserPlus className="w-4 h-4" />
                                                    </button>
                                                    <button
                                                        className="btn btn-sm btn-ghost text-red-500 hover:bg-red-500/10"
                                                        onClick={() => handleDeleteRepository(repo.id, repo.name)}
                                                        title="Delete Repository"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {showGitHubModal && (
                <div className="modal modal-open">
                    <div className="modal-box dark:bg-[#1a1d21] border dark:border-[#282f39] max-w-xl">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-bold text-lg text-white">Import from GitHub</h3>
                            <button
                                className="btn btn-sm btn-circle btn-ghost"
                                onClick={() => setShowGitHubModal(false)}
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="flex items-center gap-2 mb-4 bg-[#101822] border border-white/10 rounded px-3 py-2">
                            <Search className="w-4 h-4 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search repositories..."
                                className="bg-transparent w-full outline-none text-white"
                                value={searchRepo}
                                onChange={(e) => handleSearchRepo(e.target.value)}
                            />
                        </div>

                        <div className="max-h-80 overflow-y-auto space-y-2">
                            {loadingGhRepos && <p className="text-gray-400 text-center py-6">Loading...</p>}

                            {!loadingGhRepos && filteredGhRepos.length === 0 && ghRepos.length === 0 && (
                                <p className="text-gray-500 text-center py-6">
                                    {searchRepo ? 'No repositories found matching your search.' : 'All available repositories have already been imported.'}
                                </p>
                            )}

                            {!loadingGhRepos && filteredGhRepos.length === 0 && ghRepos.length > 0 && (
                                <p className="text-gray-500 text-center py-6">No repositories found matching your search.</p>
                            )}

                            {!loadingGhRepos && filteredGhRepos.slice(0, 5).map((repo) => (
                                <div
                                    key={repo.id}
                                    className={`p-3 rounded border cursor-pointer transition ${selectedRepo?.id === repo.id
                                        ? 'border-blue-500 bg-blue-500/10'
                                        : 'border-white/10 hover:bg-white/5'
                                        }`}
                                    onClick={() => setSelectedRepo(repo)}
                                >
                                    <div className="flex items-center gap-3">
                                        <Github className="w-5 h-5 text-gray-300" />
                                        <div>
                                            <p className="text-white font-medium">{repo.name}</p>
                                            <p className="text-xs text-gray-400">{repo.full_name}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="modal-action mt-6">
                            <button className="btn btn-ghost" onClick={() => setShowGitHubModal(false)}>
                                Cancel
                            </button>
                            <button
                                className="btn btn-primary bg-primary border-none"
                                disabled={!selectedRepo}
                                onClick={handleImportRepo}
                            >
                                Import
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {showAssignModal && selectedRepoForAssign && (
                <div className="modal modal-open">
                    <div className="modal-box dark:bg-[#1a1d21] border dark:border-[#282f39] max-w-2xl">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-bold text-lg text-white">
                                Manage Assignments - {selectedRepoForAssign.name}
                            </h3>
                            <button
                                className="btn btn-sm btn-circle btn-ghost"
                                onClick={() => {
                                    if (assignSaving) return;
                                    setShowAssignModal(false);
                                    setSelectedRepoForAssign(null);
                                    setAssignSearch('');
                                    setAssignSelectedMemberIds([]);
                                }}
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h4 className="text-sm font-semibold text-gray-400">
                                    Assign Developers
                                </h4>
                                <span className="text-xs text-gray-500">
                                    Selected: {assignSelectedMemberIds.length}
                                </span>
                            </div>

                            <div className="flex items-center gap-2 mb-2 bg-[#101822] border border-white/10 rounded px-3 py-2">
                                <Search className="w-4 h-4 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Search developers by email..."
                                    className="bg-transparent w-full outline-none text-white text-sm"
                                    value={assignSearch}
                                    onChange={(e) => setAssignSearch(e.target.value)}
                                />
                            </div>

                            {members.length === 0 ? (
                                <p className="text-sm text-gray-500">No developers available</p>
                            ) : (
                                <div className="space-y-2 max-h-64 overflow-y-auto">
                                    {members
                                        .filter((member) => {
                                            const q = assignSearch.trim().toLowerCase();
                                            if (!q) return true;
                                            return (
                                                (member.email || '').toLowerCase().includes(q) ||
                                                (member.first_name || '').toLowerCase().includes(q) ||
                                                (member.last_name || '').toLowerCase().includes(q)
                                            );
                                        })
                                        .slice(0, 10)
                                        .map((member) => {
                                            const isChecked = assignSelectedMemberIds.includes(member.id);
                                            return (
                                                <label
                                                    key={member.id}
                                                    className="flex items-center justify-between p-3 rounded border border-white/10 bg-[#0A0F16] cursor-pointer gap-3"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <input
                                                            type="checkbox"
                                                            className="checkbox checkbox-sm"
                                                            checked={isChecked}
                                                            onChange={() => {
                                                                setAssignSelectedMemberIds((prev) =>
                                                                    isChecked
                                                                        ? prev.filter((id) => id !== member.id)
                                                                        : [...prev, member.id]
                                                                );
                                                            }}
                                                            disabled={assignSaving}
                                                        />
                                                        <div>
                                                            <div className="font-medium text-white text-sm">
                                                                {member.email}
                                                            </div>
                                                            <div className="text-xs text-gray-400">
                                                                {member.first_name} {member.last_name} • {member.role}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </label>
                                            );
                                        })}
                                </div>
                            )}
                            {members.length > 0 && (
                                <p className="text-[11px] text-gray-500">
                                    Showing at most 10 matching developers. Refine your search to narrow down.
                                </p>
                            )}
                        </div>

                        <div className="modal-action mt-6">
                            <button
                                className="btn btn-ghost"
                                onClick={() => {
                                    if (assignSaving) return;
                                    setShowAssignModal(false);
                                    setSelectedRepoForAssign(null);
                                    setAssignSearch('');
                                    setAssignSelectedMemberIds([]);
                                }}
                                disabled={assignSaving}
                            >
                                Cancel
                            </button>
                            <button
                                className="btn btn-primary bg-primary border-none disabled:opacity-50"
                                disabled={assignSaving}
                                onClick={async () => {
                                    if (!selectedRepoForAssign) return;
                                    try {
                                        setAssignSaving(true);
                                        const repoId = selectedRepoForAssign.id;
                                        const currentAssignedIds = assignments[repoId] || [];
                                        const newAssignedIds = assignSelectedMemberIds;

                                        const toAssign = newAssignedIds.filter(
                                            (id) => !currentAssignedIds.includes(id)
                                        );
                                        const toUnassign = currentAssignedIds.filter(
                                            (id) => !newAssignedIds.includes(id)
                                        );

                                        // fetching current assignments once to resolve assignment IDs for unassignment
                                        let assignmentMap = {};
                                        if (toUnassign.length > 0) {
                                            const assignRes = await api.get(
                                                API_ENDPOINTS.REPOSITORY_ASSIGNMENTS(currentTenant.id, repoId)
                                            );
                                            (assignRes.data.assignments || []).forEach((a) => {
                                                assignmentMap[a.member_id] = a.id;
                                            });
                                        }

                                        // perform unassignments
                                        for (const memberId of toUnassign) {
                                            const assignmentId = assignmentMap[memberId];
                                            if (assignmentId) {
                                                await api.delete(
                                                    API_ENDPOINTS.UNASSIGN_DEVELOPER(currentTenant.id, repoId, assignmentId)
                                                );
                                            }
                                        }

                                        // perform assignments
                                        for (const memberId of toAssign) {
                                            await api.post(
                                                API_ENDPOINTS.ASSIGN_DEVELOPERS(currentTenant.id, repoId),
                                                { member_id: memberId }
                                            );
                                        }

                                        toast.success('Assignments updated successfully');
                                        await fetchRepositories();
                                        setShowAssignModal(false);
                                        setSelectedRepoForAssign(null);
                                        setAssignSearch('');
                                        setAssignSelectedMemberIds([]);
                                    } catch (error) {
                                        toast.error(
                                            error.response?.data?.error ||
                                            'Failed to update assignments'
                                        );
                                    } finally {
                                        setAssignSaving(false);
                                    }
                                }}
                            >
                                {assignSaving ? (
                                    <span className="loading loading-spinner loading-sm" />
                                ) : (
                                    'Save'
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {showRepoModal && (
                <div className="modal modal-open">
                    <div className="modal-box dark:bg-[#1a1d21] border dark:border-[#282f39]">
                        <h3 className="font-bold text-lg mb-4">Connect Repository</h3>
                        <form onSubmit={handleAddRepoSubmit} className="flex flex-col gap-4">
                            <input
                                type="text"
                                placeholder="Repository Name"
                                className="input input-bordered dark:bg-[#101822] dark:border-[#282f39]"
                                value={repoFormData.name}
                                onChange={(e) => setRepoFormData({ ...repoFormData, name: e.target.value })}
                                required
                            />
                            <input
                                type="url"
                                placeholder="Repository URL (HTTPS)"
                                className="input input-bordered dark:bg-[#101822] dark:border-[#282f39]"
                                value={repoFormData.url}
                                onChange={(e) => setRepoFormData({ ...repoFormData, url: e.target.value })}
                                required
                            />
                            <select
                                className="select select-bordered dark:bg-[#101822] dark:border-[#282f39]"
                                value={repoFormData.visibility}
                                onChange={(e) => setRepoFormData({ ...repoFormData, visibility: e.target.value })}
                            >
                                <option value="private">Private</option>
                                <option value="public">Public</option>
                            </select>
                            <div className="modal-action">
                                <button type="button" className="btn btn-ghost" onClick={() => setShowRepoModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn btn-primary bg-primary border-none">
                                    Connect
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    );
};

export default Repositories;

