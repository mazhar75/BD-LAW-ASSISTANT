import gatewayClient from '../client';
import { UserPreferences } from '@/types/auth';

interface UserProfile {
  id: number;
  username: string;
  email: string;
  fullName?: string;
  phoneNumber?: string;
  createdAt: string;
  updatedAt: string;
}


interface UserUsage {
  totalSearches: number;
  totalChats: number;
  bookmarkedLaws: number;
  thisWeek: {
    searches: number;
    chats: number;
  };
  thisMonth: {
    searches: number;
    chats: number;
  };
  recentSearches: string[];
  recentChats: Array<{
    id: string;
    title: string;
    date: string;
  }>;
}

class UserService {
  async getCurrentUser() {
    try {
      const response = await gatewayClient.get('/api/user/me');
      return response.data;
    } catch (error) {
      console.error('Failed to get current user:', error);
      throw error;
    }
  }

  async getProfile(): Promise<UserProfile> {
    try {
      const response = await gatewayClient.get('/api/user/profile');
      return response.data;
    } catch (error) {
      // Fallback to mock data for development
      return {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        fullName: 'Test User',
        phoneNumber: '+8801234567890',
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01'
      };
    }
  }

  async updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    const response = await gatewayClient.put('/api/user/profile', data);
    return response.data;
  }

  async getPreferences(): Promise<UserPreferences> {
    const response = await gatewayClient.get('/api/user/preferences');
    return response.data;
  }

  async updatePreferences(data: Partial<UserPreferences>): Promise<UserPreferences> {
    const response = await gatewayClient.put('/api/user/preferences', data);
    return response.data;
  }

  async getUsage(): Promise<any> {
    try {
      // Fetch more records (100 instead of 20) to get all recent activity
      const response = await gatewayClient.get('/api/user/usage?page=0&size=100');
      console.log('[UserService] Usage data fetched:', {
        total: response.data.totalElements,
        records: response.data.usage?.length,
        summary: response.data.summary
      });
      // Log first few endpoints to see what's being tracked
      if (response.data.usage && response.data.usage.length > 0) {
        console.log('[UserService] Sample endpoints:',
          response.data.usage.slice(0, 5).map((u: any) => ({
            endpoint: u.endpoint,
            method: u.method,
            query: u.query
          }))
        );
      }
      return response.data;
    } catch (error) {
      console.error('Failed to fetch usage data:', error);
      return {
        usage: [],
        summary: {
          totalRequests: 0,
          averageResponseTime: 0,
          topEndpoints: []
        }
      };
    }
  }

  async getDailyUsage(days: number = 30): Promise<any[]> {
    try {
      const response = await gatewayClient.get(`/api/user/usage/daily?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch daily usage:', error);
      return [];
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await gatewayClient.post('/api/user/change-password', {
      currentPassword,
      newPassword
    });
  }

  async deleteAccount(): Promise<void> {
    await gatewayClient.delete('/api/user/account');
  }
}

export const userService = new UserService();