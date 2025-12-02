import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const GuestRoute = () => {
    const { user, loading } = useAuth();

    if (loading) {
        return <div className="flex justify-center items-center h-screen"><span className="loading loading-spinner loading-lg"></span></div>;
    }

    if (user) {
        // Redirect based on role
        if (user.role === 'admin' || user.is_superuser) {
            return <Navigate to="/admin-dashboard" replace />;
        } else if (user.role === 'tenant') {
            // Ideally we check if they have orgs, but for guest route simple redirect is safer
            // We can default to org-dashboard, and let that page handle "no org" state if needed
            // Or redirect to create-org if we know they have none.
            // Since we don't have orgs in context easily without fetching, let's default to org-dashboard
            // But wait, AuthContext does have tenants state!
            // Let's use that if available.

            // Note: tenants might be empty if not fetched yet or if user has none.
            // If we want to be precise, we need to know if fetch happened.
            // For now, let's redirect to org-dashboard, and if they have no orgs, 
            // the TenantDashboard should probably prompt them to create one or redirect to create-org.
            return <Navigate to="/org-dashboard" replace />;
        } else if (user.role === 'developer') {
            return <Navigate to="/dev-dashboard" replace />;
        }

        return <Navigate to="/onboarding" replace />;
    }

    return <Outlet />;
};

export default GuestRoute;
