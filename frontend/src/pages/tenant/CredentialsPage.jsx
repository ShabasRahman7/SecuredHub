import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Github, GitBranch, Server, Key, Trash2 } from 'lucide-react';
import { toast } from 'react-toastify';
import { credentialsApi } from '../../services/credentialsApi';
import { showConfirmDialog } from '../../utils/sweetAlert';

const CredentialsPage = () => {
    const { user, tenant } = useAuth();
    const [credentials, setCredentials] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [selectedProvider, setSelectedProvider] = useState(null);

    // Provider configurations
    const providers = [
        {
            id: 'github',
            name: 'GitHub',
            icon: Github,
            color: 'bg-gray-900 hover:bg-gray-800',
            textColor: 'text-white',
            description: 'Connect to GitHub repositories',
            available: true,
            tokenName: 'OAuth Integration',
            tokenPlaceholder: 'Configured via OAuth',
            instructions: [
                'Click "Connect GitHub" to start OAuth flow',
                'Authorize SecuredHub to access your repositories',
                'Grant permissions for repository access and webhooks',
                'Integration will be automatically configured'
            ]
        },
        {
            id: 'gitlab',
            name: 'GitLab',
            icon: GitBranch,
            color: 'bg-orange-600 hover:bg-orange-700',
            textColor: 'text-white',
            description: 'Connect to GitLab repositories',
            available: false,
            tokenName: 'Access Token',
            tokenPlaceholder: 'glpat-xxxxxxxxxxxxxxxxxxxx'
        },
        {
            id: 'bitbucket',
            name: 'Bitbucket',
            icon: Server,
            color: 'bg-blue-600 hover:bg-blue-700',
            textColor: 'text-white',
            description: 'Connect to Bitbucket repositories',
            available: false,
            tokenName: 'App Password',
            tokenPlaceholder: 'ATBBxxxxxxxxxxxxxxxx'
        },
        {
            id: 'azure',
            name: 'Azure DevOps',
            icon: Server,
            color: 'bg-blue-500 hover:bg-blue-600',
            textColor: 'text-white',
            description: 'Connect to Azure DevOps repositories',
            available: false,
            tokenName: 'Personal Access Token',
            tokenPlaceholder: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        }
    ];

    const [newCredential, setNewCredential] = useState({
        name: '',
        provider: '',
        access_token: ''
    });

    useEffect(() => {
        fetchCredentials();
    }, []);

    const fetchCredentials = async () => {
        try {
            setLoading(true);
            const response = await credentialsApi.listCredentials(tenant.id);
            console.log('Credentials API Response:', response);
            console.log('Credentials data:', response.credentials);

            // Log each credential's repository count for debugging
            response.credentials?.forEach(cred => {
                console.log(`Credential "${cred.name}" - Repositories: ${cred.repositories_count}`);
            });

            setCredentials(response.credentials || []);
        } catch (error) {
            console.error('Error fetching credentials:', error);
            toast.error('Failed to load credentials');
            setCredentials([]);
        } finally {
            setLoading(false);
        }
    };

    const handleProviderSelect = (provider) => {
        if (!provider.available) {
            toast.info(`${provider.name} integration coming soon!`);
            return;
        }

        if (provider.id === 'github') {
            handleGitHubOAuth();
        } else {
            // For future providers, show modal
            setSelectedProvider(provider);
            setNewCredential({
                name: `${provider.name} Account`,
                provider: provider.id,
                access_token: ''
            });
            setShowAddModal(true);
        }
    };

    const handleGitHubOAuth = () => {
        // Check if GitHub client ID is configured
        const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID;

        if (!clientId || clientId === 'your_github_client_id') {
            toast.error('GitHub OAuth is not configured. Please set VITE_GITHUB_CLIENT_ID in your .env file.');
            console.error('GitHub OAuth Setup Required:', {
                message: 'Please configure GitHub OAuth',
                steps: [
                    '1. Create a GitHub OAuth App at https://github.com/settings/developers',
                    '2. Set VITE_GITHUB_CLIENT_ID in frontend/.env',
                    '3. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in backend/.env',
                    '4. Restart both servers'
                ]
            });
            return;
        }

        // Redirect to GitHub OAuth
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';
        const redirectUri = `${apiUrl}/auth/github/callback`;
        const scope = 'repo,read:org,admin:repo_hook';
        const state = btoa(JSON.stringify({ tenant_id: tenant.id, return_url: window.location.pathname }));

        const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}&state=${encodeURIComponent(state)}`;

        toast.info('Redirecting to GitHub for authorization...');
        window.location.href = githubAuthUrl;
    };

    const handleAddCredential = async (e) => {
        e.preventDefault();
        try {
            await credentialsApi.createCredential(tenant.id, newCredential);
            toast.success('Credential added successfully');
            setShowAddModal(false);
            setSelectedProvider(null);
            setNewCredential({ name: '', provider: '', access_token: '' });
            fetchCredentials();
        } catch (error) {
            console.error('Error adding credential:', error);
            const errorMessage = error.response?.data?.error || 'Failed to add credential';
            toast.error(errorMessage);
        }
    };

    const handleDeleteCredential = async (credential) => {
        const isGitHub = credential.provider === 'github';

        const confirmed = await showConfirmDialog({
            title: 'Delete Credential?',
            text: isGitHub
                ? `Are you sure you want to delete "${credential.name}"?\n\n⚠️ This will also revoke the token on GitHub and the application will lose access to your GitHub repositories.\n\nThis action cannot be undone.`
                : `Are you sure you want to delete "${credential.name}"? This action cannot be undone.`,
            confirmButtonText: isGitHub ? 'Yes, revoke & delete' : 'Yes, delete',
            cancelButtonText: 'Cancel',
            icon: 'warning'
        });

        if (!confirmed) return;

        try {
            if (isGitHub) {
                // For GitHub, use the revoke endpoint which also revokes on GitHub side
                await credentialsApi.revokeGitHubCredential(tenant.id, credential.id);
                toast.success('GitHub credential revoked and deleted successfully');
            } else {
                // For other providers, use regular delete
                await credentialsApi.deleteCredential(tenant.id, credential.id);
                toast.success('Credential deleted successfully');
            }

            fetchCredentials();
        } catch (error) {
            console.error('Error deleting credential:', error);
            console.error('Error status:', error.response?.status);
            console.error('Error response data:', error.response?.data);
            console.error('Full error response:', JSON.stringify(error.response?.data, null, 2));
            const errorMessage = error.response?.data?.error || error.response?.data?.message || 'Failed to delete credential';
            toast.error(errorMessage);
        }
    };



    const getProviderInfo = (providerId) => {
        return providers.find(p => p.id === providerId);
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="loading loading-spinner loading-lg"></div>
            </div>
        );
    }

    return (
        <>
            {/* Title Section */}
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">Repository Credentials</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        Manage access tokens for your code repositories.
                    </p>
                </div>
            </div>

            {/* Provider Selection Cards */}
            <div className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">Connect New Provider</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {providers.map((provider) => {
                        const IconComponent = provider.icon;
                        return (
                            <div
                                key={provider.id}
                                onClick={() => handleProviderSelect(provider)}
                                className={`
                                    relative p-6 rounded-xl border cursor-pointer transition-all duration-200
                                    ${provider.available
                                        ? `${provider.color} border-transparent hover:scale-105 hover:shadow-lg`
                                        : 'bg-[#0A0F16] border-white/10 hover:bg-white/5 cursor-not-allowed opacity-75'
                                    }
                                `}
                            >
                                {!provider.available && (
                                    <div className="absolute top-2 right-2">
                                        <span className="bg-yellow-500 text-black text-xs px-2 py-1 rounded-full font-semibold">
                                            Coming Soon
                                        </span>
                                    </div>
                                )}

                                <div className="flex flex-col items-center text-center">
                                    <IconComponent className={`w-8 h-8 mb-3 ${provider.available ? provider.textColor : 'text-gray-400'}`} />
                                    <h3 className={`font-semibold mb-2 ${provider.available ? provider.textColor : 'text-gray-400'}`}>
                                        {provider.name}
                                    </h3>
                                    <p className={`text-sm mb-3 ${provider.available ? 'text-gray-200' : 'text-gray-500'}`}>
                                        {provider.description}
                                    </p>
                                    {provider.available && provider.id === 'github' && (
                                        <button className="btn btn-sm btn-outline text-white border-white hover:bg-white hover:text-gray-900">
                                            Connect GitHub
                                        </button>
                                    )}
                                    {provider.available && provider.id === 'github' && (!import.meta.env.VITE_GITHUB_CLIENT_ID || import.meta.env.VITE_GITHUB_CLIENT_ID === 'your_github_client_id') && (
                                        <p className="text-xs text-yellow-400 mt-2">
                                            OAuth not configured
                                        </p>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Existing Credentials */}
            <div>
                <h2 className="text-xl font-semibold text-white mb-4">Your Credentials</h2>

                {credentials.length === 0 ? (
                    <div className="text-center py-12 bg-[#0A0F16] rounded-xl border border-white/10">
                        <Key className="mx-auto h-12 w-12 text-gray-500 mb-4" />
                        <h3 className="text-lg font-medium text-gray-300 mb-2">No credentials yet</h3>
                        <p className="text-gray-500 mb-4">Connect a provider above to get started.</p>
                    </div>
                ) : (
                    <div className="grid gap-4">
                        {credentials.map((credential) => {
                            const provider = getProviderInfo(credential.provider);
                            const IconComponent = provider?.icon || Key;

                            return (
                                <div key={credential.id} className="bg-[#0A0F16] rounded-xl p-6 border border-white/10">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center space-x-4">
                                            <div className={`p-3 rounded-lg ${provider?.color || 'bg-gray-700'}`}>
                                                <IconComponent className={`w-6 h-6 ${provider?.textColor || 'text-white'}`} />
                                            </div>
                                            <div>
                                                <h3 className="text-lg font-semibold text-white">{credential.name}</h3>
                                                <p className="text-gray-400 capitalize">{credential.provider} OAuth Integration</p>
                                                <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                                                    <span>Connected: {new Date(credential.created_at).toLocaleDateString()}</span>
                                                    <span>•</span>
                                                    <span>Repositories: {credential.repositories_count}</span>
                                                    <span>•</span>
                                                    <span className={credential.is_active ? 'text-green-400' : 'text-red-400'}>
                                                        {credential.is_active ? 'Active' : 'Revoked'}
                                                    </span>
                                                </div>
                                                {credential.github_account_login && (
                                                    <div className="mt-1 text-sm text-blue-400">
                                                        @{credential.github_account_login}
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        <div className="flex items-center space-x-2">
                                            <button
                                                onClick={() => handleDeleteCredential(credential)}
                                                className="btn btn-sm btn-ghost text-red-400 hover:text-red-300"
                                                title={credential.provider === 'github' ? 'Revoke & delete credential' : 'Delete credential'}
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* OAuth Info Modal - for non-GitHub providers */}
            {showAddModal && selectedProvider && selectedProvider.id !== 'github' && (
                <div className="modal modal-open">
                    <div className="modal-box bg-[#1a1d21] border border-[#282f39]">
                        <h3 className="font-bold text-lg mb-4 text-white">
                            {selectedProvider.name} Integration
                        </h3>

                        <div className="mb-4 p-4 bg-yellow-900/20 border border-yellow-700 rounded">
                            <p className="text-yellow-300 font-medium mb-2">Coming Soon!</p>
                            <p className="text-yellow-200 text-sm">
                                {selectedProvider.name} OAuth integration is currently under development.
                                We'll notify you when it becomes available.
                            </p>
                        </div>

                        {selectedProvider.instructions && (
                            <div className="mb-4 p-3 bg-blue-900/20 border border-blue-700 rounded">
                                <p className="text-sm font-medium text-blue-300 mb-2">When available, the process will be:</p>
                                <ol className="text-xs text-blue-200 space-y-1">
                                    {selectedProvider.instructions.map((instruction, index) => (
                                        <li key={index} className="flex">
                                            <span className="mr-2">{index + 1}.</span>
                                            <span>{instruction}</span>
                                        </li>
                                    ))}
                                </ol>
                            </div>
                        )}

                        <div className="modal-action">
                            <button
                                type="button"
                                className="btn btn-primary"
                                onClick={() => {
                                    setShowAddModal(false);
                                    setSelectedProvider(null);
                                }}
                            >
                                Got it
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default CredentialsPage;