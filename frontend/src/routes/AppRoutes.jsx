import { Routes, Route, Navigate } from 'react-router-dom';
import Login from '../pages/auth/Login';
import Register from '../pages/auth/Register';
import RequestAccess from '../pages/auth/RequestAccess';
import ForgotPassword from '../pages/auth/ForgotPassword';
import AcceptInvite from '../pages/AcceptInvite';
import AdminDashboard from '../pages/admin/AdminDashboard';
import AccessRequests from '../pages/admin/AccessRequests';
import Tenants from '../pages/admin/Tenants';
import AdminPlaceholder from '../pages/admin/AdminPlaceholder';
import TenantDashboard from '../pages/tenant/TenantDashboard';
import DevDashboard from '../pages/developer/DevDashboard';
import ProtectedRoute from './ProtectedRoute';
import GuestRoute from './GuestRoute';
import PublicRoute from './PublicRoute';
import LandingPage from '../pages/LandingPage';

const AppRoutes = () => {
    return (
        <Routes>
            {/* Public Routes (Invite-Only Platform) */}
            <Route element={<GuestRoute />}>
                <Route path="/login" element={<Login />} />
                <Route path="/request-access" element={<RequestAccess />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
            </Route>

            {/* Invite-Only Registration (Token Required) */}
            <Route path="/register" element={<Register />} />
            <Route path="/accept-invite/:token" element={<AcceptInvite />} />

            {/* Protected Routes */}
            <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
                <Route path="/admin-dashboard" element={<AdminDashboard />} />
                <Route path="/admin/access-requests" element={<AccessRequests />} />
                <Route path="/admin/tenants" element={<Tenants />} />

                {/* Admin Placeholders */}
                <Route path="/admin/workers" element={<AdminPlaceholder />} />
                <Route path="/admin/ai" element={<AdminPlaceholder />} />
                <Route path="/admin/audit-logs" element={<AdminPlaceholder />} />
                <Route path="/admin/settings" element={<AdminPlaceholder />} />
            </Route>

            <Route element={<ProtectedRoute allowedRoles={['owner']} />}>
                <Route path="/tenant-dashboard" element={<TenantDashboard />} />
            </Route>

            <Route element={<ProtectedRoute allowedRoles={['developer']} />}>
                <Route path="/dev-dashboard" element={<DevDashboard />} />
            </Route>

            <Route path="/" element={<PublicRoute><LandingPage /></PublicRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
};

export default AppRoutes;
