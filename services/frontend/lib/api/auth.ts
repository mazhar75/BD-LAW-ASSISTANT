import gatewayClient, { tokenManager, handleApiError } from './client';
import { LoginRequest, LoginResponse, RegisterRequest } from '@/types/auth';

export const authApi = {
  // Login user
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    try {
      console.log('authApi.login called with:', credentials);
      console.log('Gateway URL:', gatewayClient.defaults.baseURL);

      const response = await gatewayClient.post<LoginResponse>(
        '/api/auth/login',
        credentials
      );

      console.log('Login API response:', response);
      const data = response.data;

      // Store tokens
      if (data.accessToken && data.refreshToken) {
        console.log('Storing tokens...');
        tokenManager.setTokens(data.accessToken, data.refreshToken);
      }

      return data;
    } catch (error) {
      console.error('Login API error:', error);
      throw error; // Preserve the original error structure
    }
  },

  // Register new user
  register: async (userData: RegisterRequest): Promise<LoginResponse> => {
    try {
      const response = await gatewayClient.post<LoginResponse>(
        '/api/auth/register',
        userData
      );
      const data = response.data;

      // Store tokens
      if (data.accessToken && data.refreshToken) {
        tokenManager.setTokens(data.accessToken, data.refreshToken);
      }

      return data;
    } catch (error) {
      throw error; // Preserve the original error structure
    }
  },

  // Logout user
  logout: async (): Promise<void> => {
    try {
      await gatewayClient.post('/api/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      tokenManager.clearTokens();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
  },

  // Refresh token
  refreshToken: async (): Promise<{ accessToken: string; refreshToken: string }> => {
    const refreshToken = tokenManager.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await gatewayClient.post('/api/auth/refresh', null, {
        headers: {
          'Refresh-Token': refreshToken
        }
      });
      const { accessToken, refreshToken: newRefreshToken } = response.data;
      tokenManager.setTokens(accessToken, newRefreshToken || refreshToken);
      return { accessToken, refreshToken: newRefreshToken || refreshToken };
    } catch (error) {
      tokenManager.clearTokens();
      throw new Error(handleApiError(error));
    }
  },

  // Verify email
  verifyEmail: async (token: string): Promise<{ message: string }> => {
    try {
      const response = await gatewayClient.post('/api/auth/verify-email', {
        token,
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Request password reset
  requestPasswordReset: async (email: string): Promise<{ message: string }> => {
    try {
      const response = await gatewayClient.post('/api/auth/reset-password', {
        email,
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Reset password with token
  resetPassword: async (
    token: string,
    newPassword: string
  ): Promise<{ message: string }> => {
    try {
      const response = await gatewayClient.post('/api/auth/reset-password/confirm', {
        token,
        newPassword,
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
};