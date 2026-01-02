import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

const GitHubCallback = () => {
    const [searchParams] = useSearchParams();

    useEffect(() => {
        const error = searchParams.get('error');
        const githubConnected = searchParams.get('github_connected');

        // checking if we have a parent window to send message to
        const hasParent = window.opener && window.opener !== window;

        if (error) {
            let errorMessage = 'An unknown error occurred. Please try again.';
            
            switch (error) {
                case 'oauth_denied':
                    errorMessage = 'GitHub authorization was denied.';
                    break;
                case 'invalid_callback':
                    errorMessage = 'Invalid callback parameters.';
                    break;
                case 'invalid_state':
                    errorMessage = 'Invalid state parameter.';
                    break;
                case 'token_exchange_failed':
                    errorMessage = 'Failed to exchange authorization code.';
                    break;
                case 'no_access_token':
                    errorMessage = 'No access token received from GitHub.';
                    break;
                case 'github_api_failed':
                    errorMessage = 'Failed to fetch user information from GitHub.';
                    break;
                case 'oauth_processing_failed':
                    errorMessage = 'Failed to process OAuth callback.';
                    break;
                case 'oauth_not_configured':
                    errorMessage = 'GitHub OAuth is not configured on the server.';
                    break;
            }
            
            // sending error message to parent window
            if (hasParent) {
                try {
                    window.opener.postMessage({
                        type: 'github_oauth_error',
                        message: errorMessage
                    }, window.location.origin);
                } catch (e) {
                    // fallback: use localStorage if postMessage fails
                    localStorage.setItem('github_oauth_error', errorMessage);
                }
            } else {
                // fallback: use localStorage if no parent window
                localStorage.setItem('github_oauth_error', errorMessage);
            }
            
            // closing window after a short delay
            setTimeout(() => {
                if (hasParent) {
                    window.close();
                } else {
                    // if no parent, redirect to credentials page
                    window.location.href = '/tenant-dashboard/credentials';
                }
            }, 500);
            
        } else if (githubConnected === 'true') {
            // success - send message to parent and close
            if (hasParent) {
                try {
                    window.opener.postMessage({
                        type: 'github_oauth_success'
                    }, window.location.origin);
                } catch (e) {
                    // fallback: use localStorage if postMessage fails
                    localStorage.setItem('github_oauth_success', 'true');
                }
            } else {
                // fallback: use localStorage if no parent window
                localStorage.setItem('github_oauth_success', 'true');
            }
            
            // closing window after a short delay
            setTimeout(() => {
                if (hasParent) {
                    window.close();
                } else {
                    // if no parent, redirect to credentials page
                    window.location.href = '/tenant-dashboard/credentials';
                }
            }, 500);
        }
    }, [searchParams]);

    return (
        <div className="min-h-screen bg-[#05080C] flex items-center justify-center px-4">
            <div className="text-center">
                <div className="loading loading-spinner loading-lg text-primary"></div>
                <p className="text-gray-400 mt-4">Processing GitHub authorization...</p>
            </div>
        </div>
    );
};

export default GitHubCallback;