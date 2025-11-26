import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Mail, Lock, ArrowRight, RefreshCw, CheckCircle, User } from 'lucide-react';
import api from '../../api/axios';
import { toast } from 'react-toastify';

const Register = () => {
    const [step, setStep] = useState(1); // 1: Email, 2: OTP, 3: Details
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [verificationToken, setVerificationToken] = useState('');
    const [formData, setFormData] = useState({
        firstName: '',
        lastName: '',
        password: '',
        confirmPassword: ''
    });
    const [timer, setTimer] = useState(0);
    const [loading, setLoading] = useState(false);
    const [hasShownError, setHasShownError] = useState(false); // Prevent double toasts
    const navigate = useNavigate();

    useEffect(() => {
        let interval;
        if (timer > 0) {
            interval = setInterval(() => {
                setTimer((prev) => prev - 1);
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [timer]);

    const [inviteToken, setInviteToken] = useState(null);
    const location = useLocation();

    useEffect(() => {
        // Check for invite token in URL query params or location state
        const params = new URLSearchParams(location.search);
        const tokenFromUrl = params.get('invite_token');
        const tokenFromState = location.state?.invite_token;

        if (tokenFromUrl || tokenFromState) {
            const token = tokenFromUrl || tokenFromState;
            setInviteToken(token);
            // Fetch invited email from backend
            fetchInvitedEmail(token);
        } else {
            // No invite token - redirect to login
            if (!hasShownError) {
                setHasShownError(true);
                toast.error('Registration requires an invitation');
            }
            navigate('/login', { replace: true });
        }
    }, [location, navigate]);

    const fetchInvitedEmail = async (token) => {
        try {
            const response = await api.get(`/auth/verify-invite/?token=${token}`);
            setEmail(response.data.email); // Auto-fill email
            
            // Show different message based on invite type
            if (response.data.type === 'member') {
                toast.info(`You've been invited to join as a Developer`);
            } else {
                toast.info(`Signing up as: ${response.data.email}`);
            }
        } catch (err) {
            // Prevent double toast messages
            if (!hasShownError) {
                setHasShownError(true);
                toast.error('Invalid or expired invitation link');
            }
            // Use replace:true to prevent back button navigation
            navigate('/login', { replace: true });
        }
    };

    const handleSendOtp = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await api.post('/auth/send-otp/', { email, type: 'register' });
            setStep(2);
            setTimer(60);
            toast.success(`OTP sent to ${email}`);
        } catch (err) {

            const errorDetails = err.response?.data?.error?.details;
            if (errorDetails?.email) {
                toast.error(errorDetails.email[0]);
            } else if (typeof errorDetails === 'string') {
                toast.error(errorDetails);
            } else {
                toast.error(err.response?.data?.error?.message || 'Failed to send OTP');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleVerifyOtp = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await api.post('/auth/verify-otp/', { email, otp });
            setVerificationToken(response.data.verification_token);
            setStep(3);
            toast.success('OTP verified successfully');
        } catch (err) {
            toast.error(err.response?.data?.error?.message || 'Invalid OTP');
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        if (formData.password !== formData.confirmPassword) {
            toast.error("Passwords don't match");
            return;
        }
        setLoading(true);
        try {
            const payload = {
                email,
                password: formData.password,
                password2: formData.confirmPassword,
                first_name: formData.firstName,
                last_name: formData.lastName,
                verification_token: verificationToken
            };

            if (inviteToken) {
                payload.invite_token = inviteToken;
            }

            await api.post('/auth/register/', payload);

            if (inviteToken) {
                toast.success('Registration successful! You have joined the tenant.');
            } else {
                toast.success('Registration successful! Please login.');
            }
            navigate('/login');
        } catch (err) {
            toast.error(err.response?.data?.error?.message || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-base-200">
            <div className="card w-96 bg-base-100 shadow-xl">
                <div className="card-body">
                    <h2 className="card-title justify-center text-2xl font-bold mb-4">
                        Create Account
                    </h2>



                    {step === 1 && (
                        <form onSubmit={handleSendOtp}>
                            <div className="form-control w-full">
                                <label className="label"><span className="label-text">Email (Invitation)</span></label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                                    <input
                                        type="email"
                                        placeholder="user@example.com"
                                        className="input input-bordered w-full pl-10"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        disabled={inviteToken !== null}
                                        readOnly={inviteToken !== null}
                                        required
                                    />
                                </div>
                                {inviteToken && email && (
                                    <label className="label">
                                        <span className="label-text-alt text-info">
                                            This email was invited by the admin
                                        </span>
                                    </label>
                                )}
                            </div>
                            <div className="form-control mt-6">
                                <button className="btn btn-primary" disabled={loading}>
                                    {loading ? <span className="loading loading-spinner"></span> : 'Send OTP'}
                                </button>
                            </div>
                        </form>
                    )}

                    {step === 2 && (
                        <form onSubmit={handleVerifyOtp}>
                            <div className="alert alert-info text-xs py-2 mb-4">OTP sent to {email}</div>
                            <div className="form-control w-full">
                                <label className="label"><span className="label-text">Enter OTP</span></label>
                                <input
                                    type="text"
                                    placeholder="123456"
                                    className="input input-bordered w-full text-center text-2xl tracking-widest"
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value)}
                                    maxLength={6}
                                    required
                                />
                            </div>
                            <div className="form-control mt-6">
                                <button className="btn btn-primary" disabled={loading}>
                                    {loading ? <span className="loading loading-spinner"></span> : 'Verify OTP'}
                                </button>
                            </div>
                            <div className="mt-4 text-center">
                                {timer === 0 ? (
                                    <button type="button" onClick={handleSendOtp} className="btn btn-ghost btn-sm">
                                        <RefreshCw className="w-4 h-4 mr-2" /> Resend OTP
                                    </button>
                                ) : (
                                    <span className="text-sm text-gray-500">Resend in {timer}s</span>
                                )}
                            </div>
                        </form>
                    )}

                    {step === 3 && (
                        <form onSubmit={handleRegister}>
                            <div className="form-control w-full">
                                <label className="label"><span className="label-text">First Name</span></label>
                                <div className="relative">
                                    <User className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                                    <input
                                        type="text"
                                        placeholder="John"
                                        className="input input-bordered w-full pl-10"
                                        value={formData.firstName}
                                        onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                                    />
                                </div>
                            </div>
                            <div className="form-control w-full mt-2">
                                <label className="label"><span className="label-text">Last Name</span></label>
                                <div className="relative">
                                    <User className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                                    <input
                                        type="text"
                                        placeholder="Doe"
                                        className="input input-bordered w-full pl-10"
                                        value={formData.lastName}
                                        onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                                    />
                                </div>
                            </div>
                            <div className="form-control w-full mt-2">
                                <label className="label"><span className="label-text">Password</span></label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                                    <input
                                        type="password"
                                        placeholder="••••••••"
                                        className="input input-bordered w-full pl-10"
                                        value={formData.password}
                                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                        required
                                    />
                                </div>
                            </div>
                            <div className="form-control w-full mt-2">
                                <label className="label"><span className="label-text">Confirm Password</span></label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                                    <input
                                        type="password"
                                        placeholder="••••••••"
                                        className="input input-bordered w-full pl-10"
                                        value={formData.confirmPassword}
                                        onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                                        required
                                    />
                                </div>
                            </div>
                            <div className="form-control mt-6">
                                <button className="btn btn-primary" disabled={loading}>
                                    {loading ? <span className="loading loading-spinner"></span> : 'Register'}
                                </button>
                            </div>
                        </form>
                    )}

                    <div className="divider">OR</div>
                    <div className="text-center text-sm">
                        Already have an account? <Link to="/login" className="link link-primary">Login</Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Register;
