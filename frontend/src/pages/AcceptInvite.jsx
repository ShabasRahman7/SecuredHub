import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { CheckCircle, XCircle, Loader } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-toastify';

const AcceptInvite = () => {
    const { token } = useParams();
    const { user, loading: authLoading } = useAuth();
    const navigate = useNavigate();
    const [status, setStatus] = useState('verifying'); // verifying, success, error
    const [message, setMessage] = useState('Verifying invitation...');

    useEffect(() => {
        if (authLoading) return;

        if (!user) {
            // redirecting to register with invite token
            navigate(`/register?invite_token=${token}`, { state: { invite_token: token, message: 'Please create an account to accept the invitation.' } });
            return;
        }

        const acceptInvite = async () => {
            try {
                await api.post('/tenants/accept-invite/', { token });
                setStatus('success');
                setMessage('Invitation accepted successfully! Redirecting...');
                toast.success('Invitation accepted successfully!');
                setTimeout(() => navigate('/org-dashboard'), 2000);
            } catch (err) {
                setStatus('error');
                const errMsg = err.response?.data?.error?.message || 'Failed to accept invitation';
                setMessage(errMsg);
                toast.error(errMsg);
            }
        };

        acceptInvite();
    }, [token, user, authLoading, navigate]);

    if (authLoading) return <div className="min-h-screen flex items-center justify-center"><span className="loading loading-spinner loading-lg"></span></div>;

    return (
        <div className="min-h-screen flex items-center justify-center bg-base-200">
            <div className="card w-96 bg-base-100 shadow-xl">
                <div className="card-body text-center">
                    {status === 'verifying' && (
                        <>
                            <Loader className="w-12 h-12 mx-auto animate-spin text-primary mb-4" />
                            <h2 className="text-xl font-bold">Verifying Invitation</h2>
                            <p className="text-gray-500">{message}</p>
                        </>
                    )}

                    {status === 'success' && (
                        <>
                            <CheckCircle className="w-12 h-12 mx-auto text-success mb-4" />
                            <h2 className="text-xl font-bold text-success">Success!</h2>
                            <p className="text-gray-500">{message}</p>
                        </>
                    )}

                    {status === 'error' && (
                        <>
                            <XCircle className="w-12 h-12 mx-auto text-error mb-4" />
                            <h2 className="text-xl font-bold text-error">Error</h2>
                            <p className="text-gray-500 mb-4">{message}</p>
                            <Link to="/" className="btn btn-primary btn-sm">Go Home</Link>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AcceptInvite;
