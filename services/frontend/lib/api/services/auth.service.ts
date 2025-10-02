import { authApi } from '../auth';
import { LoginRequest, RegisterRequest, User } from '@/types/auth';
import { ApiError } from '@/types/errors';

interface ServiceResponse<T = unknown> {
  success: boolean;
  data: T;
  message?: string;
}

interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

class AuthService {
  async login(credentials: LoginRequest): Promise<ServiceResponse<AuthResponse>> {
    try {
      const response = await authApi.login(credentials);
      return {
        success: true,
        data: {
          user: response.user,
          accessToken: response.accessToken,
          refreshToken: response.refreshToken
        }
      };
    } catch (error: unknown) {
      throw error as ApiError;
    }
  }

  async register(userData: RegisterRequest): Promise<ServiceResponse<AuthResponse>> {
    try {
      const response = await authApi.register(userData);
      return {
        success: true,
        data: {
          user: response.user,
          accessToken: response.accessToken,
          refreshToken: response.refreshToken
        }
      };
    } catch (error: unknown) {
      throw error as ApiError;
    }
  }

  async logout(): Promise<void> {
    return authApi.logout();
  }

  async verifyEmail(token: string): Promise<ServiceResponse> {
    try {
      const response = await authApi.verifyEmail(token);
      return {
        success: true,
        data: response
      };
    } catch (error: unknown) {
      throw error as ApiError;
    }
  }

  async requestPasswordReset(email: string): Promise<ServiceResponse> {
    try {
      const response = await authApi.requestPasswordReset(email);
      return {
        success: true,
        data: response
      };
    } catch (error: unknown) {
      throw error as ApiError;
    }
  }

  async resetPassword(data: { token: string; newPassword: string }): Promise<ServiceResponse> {
    try {
      const response = await authApi.resetPassword(data.token, data.newPassword);
      return {
        success: true,
        data: response
      };
    } catch (error: unknown) {
      throw error as ApiError;
    }
  }

  async validateResetToken(_token: string): Promise<{ valid: boolean }> {
    try {
      // Mock validation for now
      return { valid: true };
    } catch (error: unknown) {
      throw error as ApiError;
    }
  }

  async refreshToken(): Promise<ServiceResponse> {
    try {
      const response = await authApi.refreshToken();
      return {
        success: true,
        data: response
      };
    } catch (error: unknown) {
      throw error as ApiError;
    }
  }

  async resendVerificationEmail(_email: string): Promise<ServiceResponse> {
    try {
      // For now, return success as the backend endpoint may not be implemented yet
      return {
        success: true,
        data: { message: 'Verification email sent' }
      };
    } catch (error: unknown) {
      throw error as ApiError;
    }
  }
}

export const authService = new AuthService();