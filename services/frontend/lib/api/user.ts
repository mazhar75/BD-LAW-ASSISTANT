import gatewayClient, { handleApiError } from './client';
import {
  User,
  UpdateProfileRequest,
  ChangePasswordRequest,
  UserPreferences,
} from '@/types/auth';

export const userApi = {
  // Get user profile
  getProfile: async (): Promise<User> => {
    try {
      const response = await gatewayClient.get<User>('/api/user/profile');
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Update user profile
  updateProfile: async (data: UpdateProfileRequest): Promise<{ message: string }> => {
    try {
      const response = await gatewayClient.put('/api/user/profile', data);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Change password
  changePassword: async (data: ChangePasswordRequest): Promise<{ message: string }> => {
    try {
      const response = await gatewayClient.post('/api/user/change-password', data);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Get user preferences
  getPreferences: async (): Promise<UserPreferences> => {
    try {
      const response = await gatewayClient.get<UserPreferences>(
        '/api/user/preferences'
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Update user preferences
  updatePreferences: async (
    preferences: Partial<UserPreferences>
  ): Promise<UserPreferences> => {
    try {
      const response = await gatewayClient.put<UserPreferences>(
        '/api/user/preferences',
        preferences
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Get usage statistics
  getUsageStats: async (startDate?: Date, endDate?: Date) => {
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('startDate', startDate.toISOString());
      if (endDate) params.append('endDate', endDate.toISOString());

      const response = await gatewayClient.get(`/api/user/usage?${params.toString()}`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
};