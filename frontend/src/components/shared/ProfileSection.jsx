import { Edit, X, Save } from 'lucide-react';

const ProfileSection = ({
  currentTenant,
  user,
  isEditingProfile,
  setIsEditingProfile,
  tenantName,
  setTenantName,
  tenantDescription,
  setTenantDescription,
  onUpdateProfile,
}) => {
  return (
    <div className="card bg-white dark:bg-[#1a1d21] border border-[#e5e7eb] dark:border-[#282f39] shadow-sm max-w-2xl">
      <div className="card-body">
        <div className="flex justify-between items-center mb-6">
          <h2 className="card-title">Tenant Profile</h2>
          {!isEditingProfile ? (
            <button
              className="btn btn-sm btn-ghost"
              onClick={() => setIsEditingProfile(true)}
            >
              <Edit className="w-4 h-4 mr-2" /> Edit
            </button>
          ) : (
            <button
              className="btn btn-sm btn-ghost text-error"
              onClick={() => setIsEditingProfile(false)}
            >
              <X className="w-4 h-4 mr-2" /> Cancel
            </button>
          )}
        </div>

        {isEditingProfile ? (
          <form onSubmit={onUpdateProfile} className="space-y-4">
            <div className="form-control">
              <label className="label">Name</label>
              <input
                type="text"
                className="input input-bordered dark:bg-[#101822] dark:border-[#282f39]"
                value={tenantName}
                onChange={(e) => setTenantName(e.target.value)}
              />
            </div>
            <div className="form-control">
              <label className="label">Description</label>
              <textarea
                className="textarea textarea-bordered dark:bg-[#101822] dark:border-[#282f39]"
                value={tenantDescription}
                onChange={(e) => setTenantDescription(e.target.value)}
              ></textarea>
            </div>
            <button type="submit" className="btn btn-primary">
              <Save className="w-4 h-4 mr-2" /> Save Changes
            </button>
          </form>
        ) : (
          <div className="space-y-6">
            <div>
              <h3 className="font-bold text-gray-500 text-xs uppercase tracking-wider mb-1">
                Organization Name
              </h3>
              <p className="text-lg font-medium">{currentTenant.name}</p>
            </div>
            <div>
              <h3 className="font-bold text-gray-500 text-xs uppercase tracking-wider mb-1">
                Description
              </h3>
              <p className="text-gray-700 dark:text-[#9da8b9]">
                {currentTenant.description || 'No description provided.'}
              </p>
            </div>
            <div className="divider"></div>
            <div>
              <h3 className="font-bold text-gray-500 text-xs uppercase tracking-wider mb-1">
                Primary Owner
              </h3>
              <div className="flex items-center gap-3 mt-2">
                <div className="bg-primary/20 rounded-full size-10 flex items-center justify-center text-primary font-bold">
                  {user?.first_name?.[0]}
                </div>
                <div>
                  <p className="font-medium">
                    {user.first_name} {user.last_name}
                  </p>
                  <p className="text-sm text-gray-500">{user.email}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfileSection;
