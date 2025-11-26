import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Shield, Eye, EyeOff } from 'lucide-react';
import { toast } from 'react-toastify';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await login(email, password);
            toast.success('Login successful!');
        } catch (err) {
            toast.error(err.response?.data?.error?.message || 'Failed to login. Please check your credentials.');
            console.error(err);
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
                                Sign in to your account
                            </h1>
                            <p className="text-gray-400 text-sm font-normal leading-normal pb-6 text-center">
                                Please enter your details to access the platform.
                            </p>

                            <form onSubmit={handleSubmit} className="flex w-full flex-col gap-3">
                                <label className="flex flex-col w-full">
                                    <p className="text-base-content text-xs font-medium leading-normal pb-1.5">Email or Username</p>
                                    <input
                                        className="input input-bordered w-full h-10 bg-base-200 focus:border-primary focus:ring-2 focus:ring-primary/50 text-sm"
                                        placeholder="Enter your email or username"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        disabled={loading}
                                    />
                                </label>
                                <label className="flex flex-col w-full">
                                    <p className="text-base-content text-xs font-medium leading-normal pb-1.5">Password</p>
                                    <div className="relative flex w-full flex-1 items-stretch">
                                        <input
                                            className="input input-bordered w-full h-10 bg-base-200 focus:border-primary focus:ring-2 focus:ring-primary/50 text-sm pr-10"
                                            placeholder="Enter your password"
                                            type={showPassword ? "text" : "password"}
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            required
                                            disabled={loading}
                                        />
                                        <button
                                            type="button"
                                            className="absolute right-0 top-0 h-full px-3 text-gray-400 hover:text-base-content transition-colors"
                                            onClick={() => setShowPassword(!showPassword)}
                                            disabled={loading}
                                        >
                                            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                        </button>
                                    </div>
                                </label>
                                <div className="flex justify-end pt-0.5">
                                    <Link to="/forgot-password" className={`text-primary text-xs font-medium leading-normal underline hover:no-underline ${loading ? 'pointer-events-none opacity-50' : ''}`}>
                                        Forgot Password?
                                    </Link>
                                </div>
                                <button
                                    className="btn btn-primary h-10 w-full text-sm font-semibold mt-2"
                                    disabled={loading}
                                >
                                    {loading ? (
                                        <span className="loading loading-spinner loading-sm"></span>
                                    ) : (
                                        'Log In'
                                    )}
                                </button>
                            </form>


                            <p className="pt-4 text-xs text-center text-gray-500">
                                Don't have an account? <Link to="/request-access" className="text-primary hover:underline">Request Access</Link>
                            </p>
                        </div>

                        <div className="flex justify-center gap-6 pt-6">
                            <a className="text-xs text-gray-500 hover:text-primary transition-colors" href="#">Terms of Service</a>
                            <a className="text-xs text-gray-500 hover:text-primary transition-colors" href="#">Privacy Policy</a>
                        </div>
                        <p className="text-xs text-center text-gray-500 pt-3">© 2024 SecuredHub. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
