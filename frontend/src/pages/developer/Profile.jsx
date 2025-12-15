import { useAuth } from '../../context/AuthContext';

const Profile = () => {
    const { user } = useAuth();

    return (
        <>
            {/* Title Section */}
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">Profile</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        View and manage your developer profile.
                    </p>
                </div>
            </div>

            {/* Profile Content */}
            <div className="card bg-white dark:bg-[#1a1d21] border border-[#e5e7eb] dark:border-[#282f39] shadow-sm max-w-2xl">
                <div className="card-body">
                    <h2 className="card-title mb-6">Developer Profile</h2>
                    <div className="space-y-6">
                        <div>
                            <h3 className="font-bold text-gray-500 text-xs uppercase tracking-wider mb-1">Name</h3>
                            <p className="text-lg font-medium">{user?.first_name} {user?.last_name}</p>
                        </div>
                        <div>
                            <h3 className="font-bold text-gray-500 text-xs uppercase tracking-wider mb-1">Email</h3>
                            <p className="text-gray-700 dark:text-[#9da8b9]">{user?.email}</p>
                        </div>
                        <div className="divider"></div>
                        <div>
                            <h3 className="font-bold text-gray-500 text-xs uppercase tracking-wider mb-1">Role</h3>
                            <p className="text-gray-700 dark:text-[#9da8b9]">Developer</p>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default Profile;


