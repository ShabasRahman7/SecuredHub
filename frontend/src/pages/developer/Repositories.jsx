import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { ExternalLink, Play, Shield } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';

const Repositories = () => {
    const { tenant } = useAuth();
    const [repos, setRepos] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchRepos = async () => {
            if (!tenant) return;
            setLoading(true);
            try {
                const response = await api.get(`/tenants/${tenant.id}/repositories/`);
                const repositories = response.data.repositories || [];
                setRepos(repositories.map(r => ({ 
                    ...r, 
                    orgName: tenant.name,
                    orgId: tenant.id 
                })));
            } catch (error) {
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

    return (
        <>
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">Repositories</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        View your assigned repositories.
                    </p>
                </div>
            </div>

            {loading && (
                <div className="flex items-center justify-center py-12">
                    <span className="loading loading-spinner loading-lg text-primary"></span>
                </div>
            )}

            {!loading && (
                <div className="bg-[#0A0F16] shadow-xl rounded-xl border border-white/10 p-6">
                    <h2 className="text-xl font-bold mb-4 flex items-center text-white">
                        <ExternalLink className="w-5 h-5 mr-2" /> Assigned Repositories ({repos.length})
                    </h2>
                    <div className="space-y-4">
                        {repos.map(repo => (
                            <div key={repo.id} className="flex flex-col md:flex-row items-center justify-between p-4 bg-[#05080C] border border-white/10 rounded-lg gap-4">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                        <h3 className="font-bold text-lg text-white">{repo.name}</h3>
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                            repo.visibility === 'private' ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'
                                        }`}>
                                            {repo.visibility}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-500 mb-1">Organization: {repo.orgName}</p>
                                    {repo.description && (
                                        <p className="text-sm text-gray-400 mb-2">{repo.description}</p>
                                    )}
                                    <div className="flex items-center gap-4 mb-2">
                                        {repo.primary_language && (
                                            <span className="text-xs text-blue-400">📝 {repo.primary_language}</span>
                                        )}
                                        {repo.stars_count > 0 && (
                                            <span className="text-xs text-yellow-400">⭐ {repo.stars_count}</span>
                                        )}
                                        {repo.forks_count > 0 && (
                                            <span className="text-xs text-gray-400">🍴 {repo.forks_count}</span>
                                        )}
                                    </div>
                                    <a href={repo.url} target="_blank" rel="noreferrer" className="text-sm hover:underline flex items-center text-blue-400">
                                        {repo.url} <ExternalLink className="w-3 h-3 ml-1" />
                                    </a>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="text-right">
                                        <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${
                                            repo.validation_status === 'valid' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                            repo.validation_status === 'invalid' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                            repo.validation_status === 'access_denied' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                                            'bg-gray-500/10 text-gray-400 border-gray-500/20'
                                        }`}>
                                            {repo.validation_status ? repo.validation_status.replace('_', ' ').toUpperCase() : 'Pending'}
                                        </span>
                                        <div className="text-xs text-gray-500 mt-1">
                                            Added {new Date(repo.created_at).toLocaleDateString()}
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
        </>
    );
};

export default Repositories;


