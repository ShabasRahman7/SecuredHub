import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Edit, X, Save } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';

const Profile = () => {
    const { user, tenant } = useAuth();
    const [currentTenant, setCurrentTenant] = useState(null);
    const [isEditingProfile, setIsEditingProfile] = useState(false);
    const [tenantName, setTenantName] = useState('');
    const [tenantDescription, setTenantDescription] = useState('');

    useEffect(() => {
        if (tenant) {
            setCurrentTenant(tenant);
            setTenantName(tenant?.name || '');
            setTenantDescription(tenant?.description || '');
        }
    }, [tenant]);

    const handleUpdateProfile = async (e) => {
        e.preventDefault();
        try {
            const res = await api.put(`/tenants/${currentTenant.id}/update/`, { name: tenantName, description: tenantDescription });
            if (res.data.success) {
                toast.success("Tenant profile updated");
                setIsEditingProfile(false);
                setCurrentTenant({ ...currentTenant, name: tenantName, description: tenantDescription });
            }
        } catch (error) {
            toast.error("Failed to update profile");
        }
    };

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
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">Organization Profile</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        Update your organization details.
                    </p>
                </div>
            </div>

            {/* Profile Content */}
            <div className="card bg-white dark:bg-[#1a1d21] border border-[#e5e7eb] dark:border-[#282f39] shadow-sm max-w-2xl">
                <div className="card-body">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="card-title">Tenant Profile</h2>
                        {!isEditingProfile ? (
                            <button className="btn btn-sm btn-ghost" onClick={() => setIsEditingProfile(true)}>
                                <Edit className="w-4 h-4 mr-2" /> Edit
                            </button>
                        ) : (
                            <button className="btn btn-sm btn-ghost text-error" onClick={() => setIsEditingProfile(false)}>
                                <X className="w-4 h-4 mr-2" /> Cancel
                            </button>
                        )}
                    </div>

                    {isEditingProfile ? (
                        <form onSubmit={handleUpdateProfile} className="space-y-4">
                            <div className="form-control">
                                <label className="label">Name</label>
                                <input type="text" className="input input-bordered dark:bg-[#101822] dark:border-[#282f39]" value={tenantName} onChange={e => setTenantName(e.target.value)} />
                            </div>
                            <div className="form-control">
                                <label className="label">Description</label>
                                <textarea className="textarea textarea-bordered dark:bg-[#101822] dark:border-[#282f39]" value={tenantDescription} onChange={e => setTenantDescription(e.target.value)}></textarea>
                            </div>
                            <button type="submit" className="btn btn-primary"><Save className="w-4 h-4 mr-2" /> Save Changes</button>
                        </form>
                    ) : (
                        <div className="space-y-6">
                            <div>
                                <h3 className="font-bold text-gray-500 text-xs uppercase tracking-wider mb-1">Organization Name</h3>
                                <p className="text-lg font-medium">{currentTenant.name}</p>
                            </div>
                            <div>
                                <h3 className="font-bold text-gray-500 text-xs uppercase tracking-wider mb-1">Description</h3>
                                <p className="text-gray-700 dark:text-[#9da8b9]">{currentTenant.description || "No description provided."}</p>
                            </div>
                            <div className="divider"></div>
                            <div>
                                <h3 className="font-bold text-gray-500 text-xs uppercase tracking-wider mb-1">Primary Owner</h3>
                                <div className="flex items-center gap-3 mt-2">
                                    <div className="bg-primary/20 rounded-full size-10 flex items-center justify-center text-primary font-bold">
                                        {user?.first_name?.[0]}
                                    </div>
                                    <div>
                                        <p className="font-medium">{user?.first_name} {user?.last_name}</p>
                                        <p className="text-sm text-gray-500">{user?.email}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
};

export default Profile;

