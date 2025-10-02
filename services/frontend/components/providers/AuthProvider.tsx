'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { tokenManager } from '@/lib/api/client';
import { userService } from '@/lib/api/services/user.service';
import { authApi } from '@/lib/api/auth';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { setUser, setLoading, isAuthenticated, clearAuth } = useAuthStore();

  useEffect(() => {
    const initAuth = async () => {
      try {
        setLoading(true);

        // Check if we have tokens stored
        const accessToken = tokenManager.getAccessToken();
        const refreshToken = tokenManager.getRefreshToken();

        // If no tokens at all, user is not authenticated
        if (!accessToken && !refreshToken) {
          clearAuth();
          setLoading(false);
          return;
        }

        // Try to restore user from localStorage first for faster load
        if (!isAuthenticated) {
          const storedAuth = localStorage.getItem('auth-storage');
          if (storedAuth) {
            try {
              const authData = JSON.parse(storedAuth);
              if (authData.state?.user && authData.state?.isAuthenticated) {
                setUser(authData.state.user);
              }
            } catch (error) {
              console.error('Error parsing stored auth:', error);
            }
          }
        }

        // If we have access token, verify it by fetching user data
        if (accessToken) {
          try {
            const userData = await userService.getCurrentUser();
            if (userData) {
              setUser(userData);
            }
          } catch (error) {
            console.error('Failed to fetch user data:', error);

            // If we have a refresh token, try to refresh
            if (refreshToken) {
              try {
                const response = await authApi.refreshToken();
                if (response.accessToken) {
                  // Try to get user data again with new token
                  const userData = await userService.getCurrentUser();
                  if (userData) {
                    setUser(userData);
                  }
                }
              } catch (refreshError) {
                console.error('Failed to refresh token:', refreshError);
                clearAuth();
              }
            } else {
              clearAuth();
            }
          }
        } else if (refreshToken) {
          // We only have refresh token, try to get new access token
          try {
            const response = await authApi.refreshToken();
            if (response.accessToken) {
              const userData = await userService.getCurrentUser();
              if (userData) {
                setUser(userData);
              }
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
  }, []);

  return <>{children}</>;
}