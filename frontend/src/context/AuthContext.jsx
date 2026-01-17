import { createContext, useState, useContext, useEffect } from 'react';
import PropTypes from 'prop-types';
import api from '../api/axios';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [tenant, setTenant] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    const fetchUser = async () => {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                setLoading(false);
                return;
            }

            const userRes = await api.get('/auth/profile/');
            setUser(userRes.data.user);

            if (!userRes.data.user.is_superuser && !userRes.data.user.is_staff) {
                try {
                    const tenantsRes = await api.get('/tenants/');
                    const userTenants = tenantsRes.data.tenants || [];
                    const userTenant = userTenants.length > 0 ? userTenants[0] : null;
                    setTenant(userTenant);

                    // checking if tenant is blocked
                    if (userTenant && !userTenant.is_active) {
                        // tenant is blocked, logout user
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        setUser(null);
                        setTenant(null);
                        navigate('/login');
                        // showing error message
                        toast.error('Your account has been blocked. Please contact the administrator.');
                        return;
                    }
                } catch (tenantError) {
                    console.error('Failed to fetch tenant:', tenantError);
                    setTenant(null);
                }
            } else {
                setTenant(null);
            }
        } catch (error) {
            console.error('Failed to fetch user or tenants:', error);
            if (error.response?.status === 403 && error.response?.data?.error?.message?.includes('blocked')) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                setUser(null);
                setTenant(null);
                navigate('/login');
                toast.error(error.response.data.error.message || 'Your account has been blocked.');
            } else {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                setUser(null);
                setTenant(null);
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUser();
    }, []);

    const login = async (email, password) => {
        const response = await api.post('/auth/login/', { email, password });
        localStorage.setItem('access_token', response.data.tokens.access);
        localStorage.setItem('refresh_token', response.data.tokens.refresh);

        const userData = response.data.user;
        setUser(userData);

        try {
            const tenantsRes = await api.get('/tenants/');
            const userTenants = tenantsRes.data.tenants || [];
            setTenant(userTenants.length > 0 ? userTenants[0] : null);
        } catch (error) {
            console.error('Failed to fetch tenant after login:', error);
            setTenant(null);
        }

        const role = userData.role;

        if (role === 'admin' || userData.is_superuser) {
            navigate('/admin-dashboard');
        } else if (role === 'owner') {
            navigate('/tenant-dashboard');
        } else if (role === 'developer') {
            navigate('/dev-dashboard');
        } else {
            navigate('/');
        }

        return response;
    };

    const logout = async () => {
        try {
            await api.post('/auth/logout/');
        } catch (error) {
            console.error('Logout API call failed:', error);
        } finally {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setUser(null);
            setTenant(null);
            navigate('/login');
        }
    };

    const role = user?.role || (user?.is_superuser ? 'admin' : null);

    return (
        <AuthContext.Provider value={{ user, role, tenant, login, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

export const useAuth = () => useContext(AuthContext);
