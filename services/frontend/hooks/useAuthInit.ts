import { useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { tokenManager } from '@/lib/api/client';
import { authApi } from '@/lib/api/auth';

export function useAuthInit() {
  const { setUser, setLoading, clearAuth } = useAuthStore();

  useEffect(() => {
    const initAuth = async () => {
      setLoading(true);

      try {
        // Check if we have tokens
        const accessToken = tokenManager.getAccessToken();
        const refreshToken = tokenManager.getRefreshToken();

        if (!accessToken && !refreshToken) {
          // No tokens, user is not authenticated
          clearAuth();
          setLoading(false);
          return;
        }

        // Try to get user info from localStorage first
        const storedAuth = localStorage.getItem('auth-storage');
        if (storedAuth) {
          try {
            const authData = JSON.parse(storedAuth);
            if (authData.state?.user) {
              setUser(authData.state.user);
            }
          } catch (error) {
            console.error('Error parsing stored auth:', error);
          }
        }

        // If we have a refresh token but no access token, try to refresh
        if (!accessToken && refreshToken) {
          try {
            const response = await authApi.refreshToken();
            if (response.accessToken) {
              // Successfully refreshed, user info should be in store
              console.log('Token refreshed successfully');
            }
          } catch (error) {
            console.error('Failed to refresh token:', error);
            clearAuth();
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        clearAuth();
      } finally {
        setLoading(false);
      }
    };

    // Only run on client side
    if (typeof window !== 'undefined') {
      initAuth();
    }
  }, [setUser, setLoading, clearAuth]);
}