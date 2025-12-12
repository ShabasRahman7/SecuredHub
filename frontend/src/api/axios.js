import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';

// Utility function to check if token is expired or about to expire
const isTokenExpired = (token) => {
    if (!token) return true;

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const currentTime = Date.now() / 1000;
        // Check if token expires in the next 5 minutes (300 seconds)
        return payload.exp < (currentTime + 300);
    } catch (error) {
        console.error('Error parsing token:', error);
        return true;
    }
};

const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

// Request interceptor - attach access token and proactively refresh if needed
api.interceptors.request.use(
    async (config) => {
        const token = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');

        // Skip token refresh for auth endpoints
        if (config.url?.includes('/auth/login/') ||
            config.url?.includes('/auth/register/') ||
            config.url?.includes('/auth/token/refresh/')) {
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        }

        // If token is expired or about to expire, try to refresh it proactively
        if (token && refreshToken && isTokenExpired(token) && !isRefreshing) {
            console.log('🔄 Proactively refreshing token before request...');

            try {
                isRefreshing = true;
                const refreshResponse = await axios.post(`${BASE_URL}/auth/token/refresh/`, {
                    refresh: refreshToken
                }, {
                    headers: { 'Content-Type': 'application/json' }
                });

                const { access, refresh: newRefresh } = refreshResponse.data;
                localStorage.setItem('access_token', access);

                if (newRefresh) {
                    localStorage.setItem('refresh_token', newRefresh);
                }

                config.headers.Authorization = `Bearer ${access}`;
                console.log('✅ Proactive token refresh successful');

            } catch (error) {
                console.error('❌ Proactive token refresh failed:', error);
                // Continue with existing token, let response interceptor handle it
                config.headers.Authorization = `Bearer ${token}`;
            } finally {
                isRefreshing = false;
            }
        } else if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Skip interceptor for login/register endpoints to allow proper error handling
        if (originalRequest.url?.includes('/auth/login/') ||
            originalRequest.url?.includes('/auth/register/')) {
            return Promise.reject(error);
        }

        if (error.response?.status === 401 && !originalRequest._retry) {
            console.log('🔄 Access token expired, attempting refresh...');

            if (isRefreshing) {
                console.log('⏳ Token refresh already in progress, queuing request...');
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                }).then(token => {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    return api(originalRequest);
                }).catch(err => Promise.reject(err));
            }

            originalRequest._retry = true;
            isRefreshing = true;

            const refreshToken = localStorage.getItem('refresh_token');

            if (!refreshToken) {
                console.log('❌ No refresh token found, redirecting to login');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');

                if (window.location.pathname !== '/login') {
                    window.location.href = '/login';
                }
                return Promise.reject(error);
            }

            try {
                // Use a fresh axios instance to avoid interceptor loops
                const refreshResponse = await axios.post(`${BASE_URL}/auth/token/refresh/`, {
                    refresh: refreshToken
                }, {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const { access, refresh: newRefresh } = refreshResponse.data;

                // Update tokens in localStorage
                localStorage.setItem('access_token', access);

                // Handle refresh token rotation (if backend sends new refresh token)
                if (newRefresh) {
                    localStorage.setItem('refresh_token', newRefresh);
                }

                // Update default headers for future requests
                api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
                originalRequest.headers.Authorization = `Bearer ${access}`;

                processQueue(null, access);
                isRefreshing = false;

                console.log('✅ Token refreshed successfully');
                return api(originalRequest);

            } catch (refreshError) {
                console.error('❌ Token refresh failed:', refreshError.response?.data || refreshError.message);

                processQueue(refreshError, null);
                isRefreshing = false;

                // Clear tokens and redirect to login
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');

                // Use a more graceful redirect that works with React Router
                if (window.location.pathname !== '/login') {
                    window.location.href = '/login';
                }

                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

export default api;
