import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import PropTypes from 'prop-types';

/**
 * PublicRoute - Prevents authenticated users from accessing public pages
 * Redirects logged-in users to their appropriate dashboard
 */
const PublicRoute = ({ children }) => {
    const { user, role, loading } = useAuth();

    if (loading) {
        return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
    }

    if (user) {
        // User is logged in, redirect to appropriate dashboard
        if (role === 'admin' || user.is_superuser) {
            return <Navigate to="/admin-dashboard" replace />;
        } else if (role === 'owner') {
            return <Navigate to="/tenant-dashboard" replace />;
        } else if (role === 'developer') {
            return <Navigate to="/dev-dashboard" replace />;
        }
        // Fallback - shouldn't reach here
        return <Navigate to="/" replace />;
    }

    // User not logged in, show the public page
    return children;
};

PublicRoute.propTypes = {
    children: PropTypes.node.isRequired,
};

export default PublicRoute;
