import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, ArrowLeft, RefreshCw, Eye, EyeOff } from 'lucide-react';
import api from '../../api/axios';
import { toast } from 'react-toastify';

const ForgotPassword = () => {
    const [step, setStep] = useState(1); // 1: Email, 2: OTP, 3: New Password
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [verificationToken, setVerificationToken] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [timer, setTimer] = useState(0);
    const [loading, setLoading] = useState(false);
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

    const handleSendOtp = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await api.post('/auth/send-otp/', { email, type: 'reset_password' });
            setStep(2);
            setTimer(60);
            toast.success(`OTP sent to ${email}`);
        } catch (err) {
            toast.error(err.response?.data?.error?.message || 'Failed to send OTP');
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

    const handleResetPassword = async (e) => {
        e.preventDefault();
        if (password !== confirmPassword) {
            toast.error("Passwords don't match");
            return;
        }
        setLoading(true);
        try {
            await api.post('/auth/reset-password/', {
                email,
                password,
                password2: confirmPassword,
                verification_token: verificationToken
            });
            toast.success('Password reset successful! Please login.');
            navigate('/login');
        } catch (err) {
            toast.error(err.response?.data?.error?.message || 'Password reset failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="relative flex h-auto min-h-screen w-full flex-col bg-base-200 overflow-x-hidden font-sans">
            <div className="layout-container flex h-full grow flex-col">
                <div className="px-4 flex flex-1 justify-center items-center py-10 sm:py-20">
                    <div className="layout-content-container flex flex-col w-full max-w-[380px] flex-1">
                        <div className="flex flex-col items-center justify-center p-6 sm:p-8 rounded-xl bg-base-100 border border-white/10 shadow-lg">
                            <div className="flex items-center gap-2 pb-2">
                                <Shield className="w-8 h-8 text-primary fill-primary/20" />
                                <h2 className="text-2xl font-bold text-base-content">SecuredHub</h2>
                            </div>
                            <h1 className="text-base-content tracking-tight text-2xl font-bold leading-tight text-center pb-2 pt-4">
                                Reset Password
                            </h1>
                            <p className="text-gray-400 text-sm font-normal leading-normal pb-6 text-center">
                                {step === 1 && "Enter your email to receive a verification code."}
                                {step === 2 && `Enter the OTP sent to ${email}.`}
                                {step === 3 && "Create a new password for your account."}
                            </p>

                            {step === 1 && (
                                <form onSubmit={handleSendOtp} className="flex w-full flex-col gap-3">
                                    <label className="flex flex-col w-full">
                                        <p className="text-base-content text-xs font-medium leading-normal pb-1.5">Email</p>
                                        <input
                                            type="email"
                                            className="input input-bordered w-full h-10 bg-base-200 focus:border-primary focus:ring-2 focus:ring-primary/50 text-sm"
                                            placeholder="user@example.com"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            required
                                        />
                                    </label>
                                    <button className="btn btn-primary h-10 w-full text-sm font-semibold mt-2" disabled={loading}>
                                        {loading ? <span className="loading loading-spinner loading-sm"></span> : 'Send OTP'}
                                    </button>
                                </form>
                            )}

                            {step === 2 && (
                                <form onSubmit={handleVerifyOtp} className="flex w-full flex-col gap-3">
                                    <label className="flex flex-col w-full">
                                        <p className="text-base-content text-xs font-medium leading-normal pb-1.5">Enter OTP</p>
                                        <input
                                            type="text"
                                            className="input input-bordered w-full h-10 bg-base-200 focus:border-primary focus:ring-2 focus:ring-primary/50 text-sm text-center tracking-widest text-xl"
                                            placeholder="123456"
                                            value={otp}
                                            onChange={(e) => setOtp(e.target.value)}
                                            maxLength={6}
                                            required
                                        />
                                    </label>
                                    <button className="btn btn-primary h-10 w-full text-sm font-semibold mt-2" disabled={loading}>
                                        {loading ? <span className="loading loading-spinner loading-sm"></span> : 'Verify OTP'}
                                    </button>
                                    <div className="mt-2 text-center">
                                        {timer === 0 ? (
                                            <button type="button" onClick={handleSendOtp} className="btn btn-ghost btn-xs text-primary hover:bg-primary/10">
                                                <RefreshCw className="w-3 h-3 mr-1" /> Resend OTP
                                            </button>
                                        ) : (
                                            <span className="text-xs text-gray-500">Resend in {timer}s</span>
                                        )}
                                    </div>
                                </form>
                            )}

                            {step === 3 && (
                                <form onSubmit={handleResetPassword} className="flex w-full flex-col gap-3">
                                    <label className="flex flex-col w-full">
                                        <p className="text-base-content text-xs font-medium leading-normal pb-1.5">New Password</p>
                                        <div className="relative flex w-full flex-1 items-stretch">
                                            <input
                                                type={showPassword ? "text" : "password"}
                                                className="input input-bordered w-full h-10 bg-base-200 focus:border-primary focus:ring-2 focus:ring-primary/50 text-sm pr-10"
                                                placeholder="••••••••"
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                required
                                            />
                                            <button
                                                type="button"
                                                className="absolute right-0 top-0 h-full px-3 text-gray-400 hover:text-base-content transition-colors"
                                                onClick={() => setShowPassword(!showPassword)}
                                            >
                                                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                            </button>
                                        </div>
                                    </label>
                                    <label className="flex flex-col w-full">
                                        <p className="text-base-content text-xs font-medium leading-normal pb-1.5">Confirm Password</p>
                                        <div className="relative flex w-full flex-1 items-stretch">
                                            <input
                                                type={showConfirmPassword ? "text" : "password"}
                                                className="input input-bordered w-full h-10 bg-base-200 focus:border-primary focus:ring-2 focus:ring-primary/50 text-sm pr-10"
                                                placeholder="••••••••"
                                                value={confirmPassword}
                                                onChange={(e) => setConfirmPassword(e.target.value)}
                                                required
                                            />
                                            <button
                                                type="button"
                                                className="absolute right-0 top-0 h-full px-3 text-gray-400 hover:text-base-content transition-colors"
                                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                            >
                                                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                            </button>
                                        </div>
                                    </label>
                                    <button className="btn btn-primary h-10 w-full text-sm font-semibold mt-2" disabled={loading}>
                                        {loading ? <span className="loading loading-spinner loading-sm"></span> : 'Reset Password'}
                                    </button>
                                </form>
                            )}

                            <div className="text-center pt-4">
                                <Link to="/login" className="text-xs font-medium text-gray-500 hover:text-primary transition-colors flex items-center justify-center gap-1">
                                    <ArrowLeft className="w-3 h-3" /> Back to Login
                                </Link>
                            </div>
                        </div>

                        <div className="flex justify-center gap-6 pt-6">
                            <a className="text-xs text-gray-500 hover:text-primary transition-colors" href="#">Terms of Service</a>
                            <a className="text-xs text-gray-500 hover:text-primary transition-colors" href="#">Privacy Policy</a>
                        </div>
                        <p className="text-xs text-center text-gray-500 pt-3">© 2024 SecurED-Hub. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ForgotPassword;
