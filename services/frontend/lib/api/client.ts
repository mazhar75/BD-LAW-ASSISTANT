import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import Cookies from 'js-cookie';
import { config } from '@/lib/config';

// Token management
export const tokenManager = {
  getAccessToken: () => {
    if (typeof window !== 'undefined') {
      return Cookies.get(config.tokenKeys.access);
    }
    return null;
  },

  getRefreshToken: () => {
    if (typeof window !== 'undefined') {
      return Cookies.get(config.tokenKeys.refresh);
    }
    return null;
  },

  setTokens: (accessToken: string, refreshToken: string) => {
    if (typeof window !== 'undefined') {
      // Set cookies with secure options
      Cookies.set(config.tokenKeys.access, accessToken, {
        expires: 1, // 1 day
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
        path: '/'
      });
      Cookies.set(config.tokenKeys.refresh, refreshToken, {
        expires: 7, // 7 days
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
        path: '/'
      });
    }
  },

  clearTokens: () => {
    if (typeof window !== 'undefined') {
      Cookies.remove(config.tokenKeys.access);
      Cookies.remove(config.tokenKeys.refresh);
      Cookies.remove(config.tokenKeys.user);
    }
  },
};

// Create axios instance for Gateway API
export const gatewayClient: AxiosInstance = axios.create({
  baseURL: config.gatewayUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create axios instance for direct RAG API (if needed)
export const ragClient: AxiosInstance = axios.create({
  baseURL: config.ragUrl,
  timeout: 60000, // Longer timeout for RAG operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
gatewayClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenManager.getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for token refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: string | null) => void;
  reject: (reason: AxiosError) => void;
}> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

gatewayClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue the request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return gatewayClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = tokenManager.getRefreshToken();

      if (!refreshToken) {
        // No refresh token, redirect to login
        tokenManager.clearTokens();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${config.gatewayUrl}/api/auth/refresh`, null, {
          headers: {
            'Refresh-Token': refreshToken
          }
        });

        const { accessToken, refreshToken: newRefreshToken } = response.data;
        tokenManager.setTokens(accessToken, newRefreshToken);
        processQueue(null, accessToken);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        }
        return gatewayClient(originalRequest);
      } catch (refreshError) {
        console.error('Token refresh failed, redirecting to login');
        processQueue(refreshError as AxiosError, null);
        tokenManager.clearTokens();

        // Clear auth store as well
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth-storage');
          // Only redirect if not already on login page
          if (!window.location.pathname.startsWith('/login')) {
            window.location.href = '/login';
          }
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// API error handler
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    if (error.response?.data?.error) {
      return error.response.data.error;
    }
    if (error.response?.data?.message) {
      return error.response.data.message;
    }
    if (error.response?.status === 404) {
      return 'Resource not found';
    }
    if (error.response?.status === 500) {
      return 'Server error occurred';
    }
    if (error.message === 'Network Error') {
      return 'Network error - please check your connection';
    }
  }
  return (error as Error).message || 'An unexpected error occurred';
};

export default gatewayClient;