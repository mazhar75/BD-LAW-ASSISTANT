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

  async getUsage(): Promise<UserUsage> {
    // Mock data for development
    return {
      totalSearches: 142,
      totalChats: 38,
      bookmarkedLaws: 27,
      thisWeek: {
        searches: 12,
        chats: 5
      },
      thisMonth: {
        searches: 48,
        chats: 15
      },
      recentSearches: [
        'Constitution Article 32',
        'Labour Act 2006',
        'Criminal Procedure Code'
      ],
      recentChats: [
        {
          id: '1',
          title: 'Rights under Constitution',
          date: '2025-09-19'
        },
        {
          id: '2',
          title: 'Labor law violations',
          date: '2025-09-18'
        }
      ]
    };
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