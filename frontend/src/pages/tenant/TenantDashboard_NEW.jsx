import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import TenantSidebar from '../../components/tenant/TenantSidebar';
import ProfileSection from '../../components/tenant/ProfileSection';
import InviteModal from '../../components/tenant/modals/InviteModal';
import AddRepoModal from '../../components/tenant/modals/AddRepoModal';
import AssignDevsModal from '../../components/tenant/modals/AssignDevsModal';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { Search, Bell, HelpCircle, Github, UserPlus, Menu, Link as LinkIcon, Trash2, Mail, X, Edit } from 'lucide-react';
import { useTenantData } from '../../hooks/useTenantData';
import { useMembers } from '../../hooks/useMembers';
import { useRepositories } from '../../hooks/useRepositories';
import { useInvites } from '../../hooks/useInvites';

const TenantDashboard = () => {
    const { user, tenants, logout } = useAuth();
    const [activeTab, setActiveTab] = useState('dashboard');
    const [sidebarOpen, setSidebarOpen] = useState(false);

    // Custom hooks for data management
    const {
        currentTenant,
        isEditingProfile,
        setIsEditingProfile,
        tenantName,
        setTenantName,
        tenantDescription,
        setTenantDescription,
        updateProfile,
    } = useTenantData(tenants);

    const { members, removeMember } = useMembers(currentTenant);
    const { repositories, addRepository, assignDevelopers } = useRepositories(currentTenant);
    const { invites, resendingInvite, sendInvite, resendInvite, cancelInvite } = useInvites(currentTenant, activeTab);

    // Modal states
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [showRepoModal, setShowRepoModal] = useState(false);
    const [showAssignModal, setShowAssignModal] = useState(false);
    const [selectedRepo, setSelectedRepo] = useState(null);

    // Loading state
    if (!currentTenant) {
        return (
            <div className="h-screen flex flex-col items-center justify-center bg-[#05080C] text-white">
                <LoadingSpinner text="Loading tenant data..." />
                {tenants.length === 0 && (
                    <p className="text-sm text-gray-400 mt-4">
                        No tenants found. You may need to be invited to a tenant first.
                    </p>
                )}
            </div>
        );
    }

    return (
        <div className="flex h-screen w-full bg-[#05080C] text-white font-sans overflow-hidden">
            {/* Sidebar */}
            <TenantSidebar
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                logout={logout}
                user={user}
                tenantName={currentTenant.name}
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
            />

            {/* Main Content */}
            <div className="flex flex-1 flex-col overflow-y-auto relative w-full">
                {/* Header */}
                <header className="flex sticky top-0 z-10 items-center justify-between whitespace-nowrap border-b border-white/10 px-6 py-3 bg-[#05080C]/80 backdrop-blur-sm">
                    <div className="flex items-center gap-4 lg:gap-8">
                        <button
                            className="lg:hidden p-2 -ml-2 text-gray-400 hover:text-white"
                            onClick={() => setSidebarOpen(true)}
                        >
                            <Menu className="w-6 h-6" />
                        </button>
                        <div className="flex items-center gap-3">
                            <h2 className="text-lg font-bold leading-tight text-white">SecuredHub</h2>
                        </div>
                        <label className="hidden md:flex flex-col min-w-40 !h-10 max-w-64">
                            <div className="flex w-full flex-1 items-stretch rounded-lg h-full bg-[#0A0F16] border border-white/10">
                                <div className="text-gray-400 flex items-center justify-center pl-3">
                                    <Search className="w-5 h-5" />
                                </div>
                                <input
                                    className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg bg-transparent h-full placeholder:text-gray-500 pl-2 text-base outline-none border-none text-white"
                                    placeholder="Search"
                                />
                            </div>
                        </label>
                    </div>
                    <div className="flex flex-1 justify-end gap-3 lg:gap-4 items-center">
                        <button className="hidden sm:flex cursor-pointer items-center justify-center rounded-full h-10 w-10 text-gray-400 hover:bg-white/10 hover:text-white transition-colors">
                            <Bell className="w-5 h-5" />
                        </button>
                        <button className="hidden sm:flex cursor-pointer items-center justify-center rounded-full h-10 w-10 text-gray-400 hover:bg-white/10 hover:text-white transition-colors">
                            <HelpCircle className="w-5 h-5" />
                        </button>
                        <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 bg-primary/20 flex items-center justify-center text-primary font-bold">
                            {user?.first_name?.[0]}
                        </div>
                    </div>
                </header>

                <main className="flex-1 p-4 lg:p-8">
                    <div className="max-w-7xl mx-auto space-y-6 lg:space-y-8">
                        {/* Title Section */}
                        <div className="flex flex-wrap justify-between items-center gap-4">
                            <div className="flex min-w-72 flex-col gap-1">
                                <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">
                                    {activeTab === 'dashboard' ? 'Organization Dashboard' :
                                        activeTab === 'repositories' ? 'Repositories' :
                                            activeTab === 'developers' ? 'Team Management' :
                                                activeTab === 'profile' ? 'Organization Profile' :
                                                    activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
                                </p>
                                <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                                    {activeTab === 'dashboard' ? 'Overview of your organization security posture.' :
                                        activeTab === 'repositories' ? 'Manage and connect your code repositories.' :
                                            activeTab === 'developers' ? 'Manage access and roles for your organization.' :
                                                activeTab === 'profile' ? 'Update your organization details.' : 'Manage your organization settings.'}
                                </p>
                            </div>
                        </div>

                        {/* Action Buttons */}
                        {activeTab === 'repositories' && (
                            <div className="flex flex-wrap gap-3 justify-start">
                                <button
                                    onClick={() => setShowRepoModal(true)}
                                    className="flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-[#136dec] text-white text-sm font-bold gap-2 hover:bg-blue-600 transition-colors"
                                >
                                    <Github className="w-4 h-4" />
                                    <span className="truncate">Add Repository</span>
                                </button>
                            </div>
                        )}
                        {activeTab === 'developers' && (
                            <div className="flex flex-wrap gap-3 justify-start">
                                <button
                                    onClick={() => setShowInviteModal(true)}
                                    className="flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold gap-2 hover:bg-blue-600 transition-colors"
                                >
                                    <UserPlus className="w-4 h-4" />
                                    <span className="truncate">Invite Developer</span>
                                </button>
                            </div>
                        )}

                        {/* Tab Content - Will be split into separate components */}
                        {activeTab === 'profile' && (
                            <ProfileSection
                                currentTenant={currentTenant}
                                user={user}
                                isEditingProfile={isEditingProfile}
                                setIsEditingProfile={setIsEditingProfile}
                                tenantName={tenantName}
                                setTenantName={setTenantName}
                                tenantDescription={tenantDescription}
                                setTenantDescription={setTenantDescription}
                                onUpdateProfile={updateProfile}
                            />
                        )}

                        {/* Other tabs will be added in separate components */}
                        {activeTab === 'dashboard' && <div>Dashboard content (to be extracted)</div>}
                        {activeTab === 'repositories' && <div>Repositories content (to be extracted)</div>}
                        {activeTab === 'developers' && <div>Developers content (to be extracted)</div>}
                    </div>
                </main>
            </div>

            {/* Modals */}
            <InviteModal
                isOpen={showInviteModal}
                onClose={() => setShowInviteModal(false)}
                onInvite={sendInvite}
            />

            <AddRepoModal
                isOpen={showRepoModal}
                onClose={() => setShowRepoModal(false)}
                onAdd={addRepository}
            />

            <AssignDevsModal
                isOpen={showAssignModal}
                onClose={() => setShowAssignModal(false)}
                onAssign={assignDevelopers}
                members={members}
                selectedRepo={selectedRepo}
            />
        </div>
    );
};

export default TenantDashboard;
