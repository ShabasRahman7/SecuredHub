import { Routes, Route, Navigate } from 'react-router-dom';
import Login from '../pages/auth/Login';
import Register from '../pages/auth/Register';
import RequestAccess from '../pages/auth/RequestAccess';
import ForgotPassword from '../pages/auth/ForgotPassword';
import AcceptInvite from '../pages/AcceptInvite';
import AdminDashboard from '../pages/admin/AdminDashboard';
import AccessRequests from '../pages/admin/AccessRequests';
import Tenants from '../pages/admin/Tenants';
import WorkerMonitoring from '../pages/admin/WorkerMonitoring';
import AdminPlaceholder from '../pages/admin/AdminPlaceholder';
import TenantDashboard from '../pages/tenant/Dashboard';
import TenantRepositories from '../pages/tenant/Repositories';
import TenantDevelopers from '../pages/tenant/Developers';
import TenantCredentials from '../pages/tenant/CredentialsPage';
import TenantScans from '../pages/tenant/Scans';
import TenantReports from '../pages/tenant/Reports';
import TenantSettings from '../pages/tenant/Settings';
import TenantProfile from '../pages/tenant/Profile';
import DevDashboard from '../pages/developer/Dashboard';
import DevRepositories from '../pages/developer/Repositories';
import DevScans from '../pages/developer/Scans';
import DevScanResults from '../pages/developer/ScanResults';
import DevVulnerabilities from '../pages/developer/Vulnerabilities';
import DevAIAssistant from '../pages/developer/AIAssistant';
import DevSettings from '../pages/developer/Settings';
import DevProfile from '../pages/developer/Profile';
import Notifications from '../pages/shared/Notifications';
import ProtectedRoute from './ProtectedRoute';
import GuestRoute from './GuestRoute';
import PublicRoute from './PublicRoute';
import LandingPage from '../pages/LandingPage';
import GitHubCallback from '../pages/auth/GitHubCallback';
import Layout from '../layouts/Layout';
import AdminLayout from '../layouts/AdminLayout';
import TenantLayout from '../layouts/TenantLayout';
import DeveloperLayout from '../layouts/DeveloperLayout';

// main application router wiring up auth, admin, tenant, and developer areas.
const AppRoutes = () => {
    return (
        <Routes>
            <Route element={<GuestRoute />}>
                <Route path="/login" element={<Login />} />
                <Route path="/request-access" element={<RequestAccess />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
            </Route>

            <Route path="/register" element={<Register />} />
            <Route path="/accept-invite/:token" element={<AcceptInvite />} />

            <Route path="/auth/github/callback" element={<GitHubCallback />} />

            <Route
                path="/admin"
                element={
                    <ProtectedRoute allowedRoles={['admin']}>
                        <AdminLayout />
                    </ProtectedRoute>
                }
            >
                <Route index element={<Navigate to="/admin/dashboard" replace />} />
                <Route path="dashboard" element={<AdminDashboard />} />
                <Route path="access-requests" element={<AccessRequests />} />
                <Route path="tenants" element={<Tenants />} />
                <Route path="notifications" element={<Notifications />} />
                <Route path="workers" element={<WorkerMonitoring />} />
                <Route path="ai" element={<AdminPlaceholder />} />
                <Route path="audit-logs" element={<AdminPlaceholder />} />
                <Route path="settings" element={<AdminPlaceholder />} />
            </Route>

            <Route path="/admin-dashboard" element={<Navigate to="/admin/dashboard" replace />} />

            <Route
                path="/tenant-dashboard"
                element={
                    <ProtectedRoute allowedRoles={['owner']}>
                        <TenantLayout />
                    </ProtectedRoute>
                }
            >
                <Route index element={<TenantDashboard />} />
                <Route path="repositories" element={<TenantRepositories />} />
                <Route path="scans" element={<TenantScans />} />
                <Route path="reports" element={<TenantReports />} />
                <Route path="notifications" element={<Notifications />} />
                <Route path="developers" element={<TenantDevelopers />} />
                <Route path="credentials" element={<TenantCredentials />} />
                <Route path="settings" element={<TenantSettings />} />
                <Route path="profile" element={<TenantProfile />} />
            </Route>

            <Route
                path="/dev-dashboard"
                element={
                    <ProtectedRoute allowedRoles={['developer']}>
                        <DeveloperLayout />
                    </ProtectedRoute>
                }
            >
                <Route index element={<DevDashboard />} />
                <Route path="repositories" element={<DevRepositories />} />
                <Route path="scans" element={<DevScans />} />
                <Route path="scans/:scanId" element={<DevScanResults />} />
                <Route path="vulnerabilities" element={<DevVulnerabilities />} />
                <Route path="notifications" element={<Notifications />} />
                <Route path="ai-assistant" element={<DevAIAssistant />} />
                <Route path="ai-assistant/:findingId" element={<DevAIAssistant />} />
                <Route path="settings" element={<DevSettings />} />
                <Route path="profile" element={<DevProfile />} />
            </Route>

            <Route path="/" element={<Layout />}>
                <Route index element={<PublicRoute><LandingPage /></PublicRoute>} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
};

export default AppRoutes;
