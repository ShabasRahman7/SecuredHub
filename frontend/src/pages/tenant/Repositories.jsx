import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Link as LinkIcon, Trash2, Github, Search, X } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';
import { showConfirmDialog, showSuccessToast, showErrorToast } from '../../utils/sweetAlert';
import { tenantService } from '../../api/services/tenantService';
import { credentialsApi } from '../../services/credentialsApi';

const Repositories = () => {
    const { tenant } = useAuth();
    const [currentTenant, setCurrentTenant] = useState(null);
    const [repositories, setRepositories] = useState([]);
    const [showGitHubModal, setShowGitHubModal] = useState(false);
    const [showRepoModal, setShowRepoModal] = useState(false);
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
        }
    }, [currentTenant]);

    const fetchRepositories = async () => {
        if (!currentTenant) return;
        try {
            const res = await api.get(`/tenants/${currentTenant.id}/repositories/`);
            setRepositories(res.data.repositories || []);
        } catch (error) {
            console.error("Failed to fetch repositories", error);
        }
    };

    const handleAddRepo = async (repoData) => {
        try {
            await api.post(`/tenants/${currentTenant.id}/repositories/create/`, repoData);
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
            console.error('Failed to delete repository', error);
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
            console.error('Failed to fetch GitHub repos', err);
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
            console.error('Import failed', err);
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
            {/* Title Section */}
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">Repositories</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        Manage and connect your code repositories.
                    </p>
                </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3 justify-start">
                <button
                    onClick={() => setShowGitHubModal(true)}
                    className="flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-[#136dec] text-white text-sm font-bold gap-2 hover:bg-blue-600 transition-colors"
                >
                    <Github className="w-4 h-4" />
                    <span>Import from GitHub</span>
                </button>
            </div>

            {/* Repositories Grid */}
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
                                <button 
                                    className="btn btn-sm btn-ghost text-red-500 hover:bg-red-500/10" 
                                    onClick={() => handleDeleteRepository(repo.id, repo.name)}
                                    title="Delete Repository"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                    {repositories.length === 0 && <div className="col-span-full text-center py-10 text-gray-500">No repositories connected. Add one to get started.</div>}
                </div>
            </div>

            {/* GitHub Import Modal */}
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
                                    className={`p-3 rounded border cursor-pointer transition ${
                                        selectedRepo?.id === repo.id 
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

            {/* Add Repository Modal */}
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

