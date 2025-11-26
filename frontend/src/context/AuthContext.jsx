import { createContext, useState, useContext, useEffect } from 'react';
import PropTypes from 'prop-types';
import api from '../api/axios';
import { useNavigate } from 'react-router-dom'; // Added useNavigate

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [tenants, setTenants] = useState([]); // Added tenants state
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate(); // Added useNavigate hook

    const fetchUser = async () => {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                setLoading(false);
                return;
            }

            const userRes = await api.get('/auth/profile/');
            setUser(userRes.data.user);

            // Fetch tenants
            const tenantsRes = await api.get('/tenants/');
            setTenants(tenantsRes.data.tenants || []);
        } catch (error) {
            console.error('Failed to fetch user or tenants:', error);
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setUser(null);
            setTenants([]);
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

        // Fetch tenants immediately after login
        try {
            const tenantsRes = await api.get('/tenants/');
            setTenants(tenantsRes.data.tenants || []);
        } catch (error) {
            console.error('Failed to fetch tenants after login:', error);
            setTenants([]);
        }

        // Determine redirection based on role
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

    const logout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
    };

    // Derive role directly from user object
    const role = user?.role || (user?.is_superuser ? 'admin' : null);

    return (
        <AuthContext.Provider value={{ user, role, tenants, login, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

export const useAuth = () => useContext(AuthContext);
