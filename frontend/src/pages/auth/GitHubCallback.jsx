import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import { Github, CheckCircle, XCircle, Loader } from 'lucide-react';

const GitHubCallback = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [status, setStatus] = useState('processing'); // processing, success, error
    const [message, setMessage] = useState('Processing GitHub authorization...');

    useEffect(() => {
        const handleCallback = () => {
            const error = searchParams.get('error');
            const githubConnected = searchParams.get('github_connected');
            const credentialId = searchParams.get('credential_id');

            if (error) {
                setStatus('error');
                switch (error) {
                    case 'oauth_denied':
                        setMessage('GitHub authorization was denied. Please try again.');
                        break;
                    case 'invalid_callback':
                        setMessage('Invalid callback parameters. Please try again.');
                        break;
                    case 'invalid_state':
                        setMessage('Invalid state parameter. Please try again.');
                        break;
                    case 'token_exchange_failed':
                        setMessage('Failed to exchange authorization code. Please try again.');
                        break;
                    case 'no_access_token':
                        setMessage('No access token received from GitHub. Please try again.');
                        break;
                    case 'github_api_failed':
                        setMessage('Failed to fetch user information from GitHub. Please try again.');
                        break;
                    case 'oauth_processing_failed':
                        setMessage('Failed to process OAuth callback. Please try again.');
                        break;
                    default:
                        setMessage('An unknown error occurred. Please try again.');
                }
                
                toast.error('GitHub connection failed');
                
                // Redirect to dashboard after 3 seconds
                setTimeout(() => {
                    navigate('/tenant-dashboard');
                }, 3000);
                
            } else if (githubConnected === 'true') {
                setStatus('success');
                setMessage('GitHub successfully connected! You can now access your repositories.');
                
                toast.success('GitHub connected successfully!');
                
                // Redirect to dashboard after 2 seconds
                setTimeout(() => {
                    navigate('/tenant-dashboard');
                }, 2000);
                
            } else {
                setStatus('error');
                setMessage('Unexpected callback state. Please try again.');
                
                setTimeout(() => {
                    navigate('/tenant-dashboard');
                }, 3000);
            }
        };

        handleCallback();
    }, [searchParams, navigate]);

    const getIcon = () => {
        switch (status) {
            case 'processing':
                return <Loader className="w-16 h-16 text-blue-500 animate-spin" />;
            case 'success':
                return <CheckCircle className="w-16 h-16 text-green-500" />;
            case 'error':
                return <XCircle className="w-16 h-16 text-red-500" />;
            default:
                return <Github className="w-16 h-16 text-gray-500" />;
        }
    };

    const getStatusColor = () => {
        switch (status) {
            case 'processing':
                return 'text-blue-600';
            case 'success':
                return 'text-green-600';
            case 'error':
                return 'text-red-600';
            default:
                return 'text-gray-600';
        }
    };

    return (
        <div className="min-h-screen bg-[#05080C] flex items-center justify-center px-4">
            <div className="max-w-md w-full">
                <div className="bg-gray-800 rounded-lg p-8 text-center border border-gray-700">
                    <div className="flex justify-center mb-6">
                        {getIcon()}
                    </div>
                    
                    <h1 className={`text-2xl font-bold mb-4 ${getStatusColor()}`}>
                        {status === 'processing' && 'Connecting GitHub...'}
                        {status === 'success' && 'Connection Successful!'}
                        {status === 'error' && 'Connection Failed'}
                    </h1>
                    
                    <p className="text-gray-300 mb-6">
                        {message}
                    </p>
                    
                    {status === 'processing' && (
                        <div className="flex items-center justify-center space-x-2 text-blue-400">
                            <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                            <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                    )}
                    
                    {status !== 'processing' && (
                        <button
                            onClick={() => navigate('/tenant-dashboard')}
                            className="btn btn-primary"
                        >
                            Continue to Dashboard
                        </button>
                    )}
                </div>
                
                <div className="text-center mt-6">
                    <p className="text-gray-500 text-sm">
                        You will be redirected automatically in a few seconds...
                    </p>
                </div>
            </div>
        </div>
    );
};

export default GitHubCallback;