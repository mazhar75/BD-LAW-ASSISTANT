import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserPreferences } from '@/types/auth';
import { userApi } from '@/lib/api';

interface PreferencesStore {
  // State
  preferences: UserPreferences | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setPreferences: (preferences: UserPreferences) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // API Actions
  loadPreferences: () => Promise<void>;
  updatePreferences: (updates: Partial<UserPreferences>) => Promise<void>;

  // Local preference actions (without API)
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setLanguage: (language: 'en' | 'bn') => void;
  setSearchType: (searchType: 'keyword' | 'semantic' | 'hybrid') => void;
  setResultsPerPage: (count: number) => void;
  toggleNotifications: (type: 'email' | 'push', enabled: boolean) => void;

  // Helper functions
  applyTheme: (theme: 'light' | 'dark' | 'system') => void;
}

const defaultPreferences: UserPreferences = {
  language: 'en',
  theme: 'system',
  searchType: 'hybrid',
  resultsPerPage: 10,
  enableNotifications: true,
  emailNotifications: true,
};

export const usePreferencesStore = create<PreferencesStore>()(
  persist(
    (set, get) => ({
      // Initial state
      preferences: defaultPreferences,
      isLoading: false,
      error: null,

      // Actions
      setPreferences: (preferences) => {
        set({ preferences });
        // Apply theme
        if (preferences.theme) {
          get().applyTheme(preferences.theme);
        }
      },

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      // API Actions
      loadPreferences: async () => {
        try {
          set({ isLoading: true, error: null });
          const preferences = await userApi.getPreferences();
          get().setPreferences(preferences);
        } catch (error: any) {
          // Use default preferences if API fails
          set({ error: error.message, preferences: defaultPreferences });
        } finally {
          set({ isLoading: false });
        }
      },

      updatePreferences: async (updates) => {
        const state = get();
        const updatedPreferences = { ...state.preferences!, ...updates };

        try {
          set({ isLoading: true, error: null });
          const preferences = await userApi.updatePreferences(updates);
          get().setPreferences(preferences);
        } catch (error: any) {
          set({ error: error.message });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      // Local preference actions
      setTheme: (theme) => {
        set((state) => ({
          preferences: state.preferences ? { ...state.preferences, theme } : null,
        }));
        get().applyTheme(theme);
        // Save to API in background
        get().updatePreferences({ theme }).catch(console.error);
      },

      setLanguage: (language) => {
        set((state) => ({
          preferences: state.preferences ? { ...state.preferences, language } : null,
        }));
        // Save to API in background
        get().updatePreferences({ language }).catch(console.error);
      },

      setSearchType: (searchType) => {
        set((state) => ({
          preferences: state.preferences ? { ...state.preferences, searchType } : null,
        }));
        // Save to API in background
        get().updatePreferences({ searchType }).catch(console.error);
      },

      setResultsPerPage: (resultsPerPage) => {
        set((state) => ({
          preferences: state.preferences ? { ...state.preferences, resultsPerPage } : null,
        }));
        // Save to API in background
        get().updatePreferences({ resultsPerPage }).catch(console.error);
      },

      toggleNotifications: (type, enabled) => {
        const field = type === 'email' ? 'emailNotifications' : 'enableNotifications';
        set((state) => ({
          preferences: state.preferences ? { ...state.preferences, [field]: enabled } : null,
        }));
        // Save to API in background
        get().updatePreferences({ [field]: enabled }).catch(console.error);
      },

      // Helper function to apply theme
      applyTheme: (theme: 'light' | 'dark' | 'system') => {
        if (typeof window === 'undefined') return;

        const root = document.documentElement;
        let resolvedTheme = theme;

        if (theme === 'system') {
          resolvedTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark'
            : 'light';
        }

        if (resolvedTheme === 'dark') {
          root.classList.add('dark');
        } else {
          root.classList.remove('dark');
        }
      },
    }),
    {
      name: 'preferences-storage',
      partialize: (state) => ({
        preferences: state.preferences,
      }),
    }
  )
);