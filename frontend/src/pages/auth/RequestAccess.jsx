import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';

const RequestAccess = () => {
    const [formData, setFormData] = useState({
        fullName: '',
        workEmail: '',
        companyName: ''
    });

    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await api.post('/auth/request-access/', {
                full_name: formData.fullName,
                email: formData.workEmail,
                company_name: formData.companyName
            });
            toast.success('Request received. We will contact you shortly.');
            setFormData({ fullName: '', workEmail: '', companyName: '' });
        } catch (err) {
            const errorMsg = err.response?.data?.error?.message || 'Failed to submit request';
            toast.error(errorMsg);
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
                                Request Access
                            </h1>
                            <p className="text-gray-400 text-sm font-normal leading-normal pb-6 text-center">
                                Fill out the form below to request an invitation. Access is granted by an administrator.
                            </p>

                            <form onSubmit={handleSubmit} className="flex w-full flex-col gap-3">
                                <label className="flex flex-col w-full">
                                    <p className="text-base-content text-xs font-medium leading-normal pb-1.5">Full Name</p>
                                    <input
                                        className="input input-bordered w-full h-10 bg-base-200 focus:border-primary focus:ring-2 focus:ring-primary/50 text-sm"
                                        placeholder="Enter your full name"
                                        value={formData.fullName}
                                        onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                                        required
                                        disabled={loading}
                                    />
                                </label>
                                <label className="flex flex-col w-full">
                                    <p className="text-base-content text-xs font-medium leading-normal pb-1.5">Work Email</p>
                                    <input
                                        className="input input-bordered w-full h-10 bg-base-200 focus:border-primary focus:ring-2 focus:ring-primary/50 text-sm"
                                        placeholder="Enter your work email"
                                        type="email"
                                        value={formData.workEmail}
                                        onChange={(e) => setFormData({ ...formData, workEmail: e.target.value })}
                                        required
                                        disabled={loading}
                                    />
                                </label>
                                <label className="flex flex-col w-full">
                                    <p className="text-base-content text-xs font-medium leading-normal pb-1.5">Company Name</p>
                                    <input
                                        className="input input-bordered w-full h-10 bg-base-200 focus:border-primary focus:ring-2 focus:ring-primary/50 text-sm"
                                        placeholder="Enter your company name"
                                        value={formData.companyName}
                                        onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                                        required
                                        disabled={loading}
                                    />
                                </label>
                                <button
                                    className="btn btn-primary h-10 w-full text-sm font-semibold mt-2"
                                    disabled={loading}
                                >
                                    {loading ? (
                                        <span className="loading loading-spinner loading-sm"></span>
                                    ) : (
                                        'Send Signup Request'
                                    )}
                                </button>
                            </form>

                            <div className="text-center pt-4">
                                <p className="text-xs text-gray-500">
                                    Already have an account? <Link to="/login" className="font-medium text-primary hover:underline">Log In</Link>
                                </p>
                            </div>
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

export default RequestAccess;
