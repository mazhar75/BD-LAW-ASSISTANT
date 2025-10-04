import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { SearchResult, SearchFilters } from '@/types/search.types';
import { searchService } from '@/lib/api/search.service';

interface SearchStore {
  // State
  query: string;
  searchType: 'keyword' | 'semantic' | 'hybrid';
  filters: SearchFilters;
  results: SearchResult[];
  totalResults: number;
  currentPage: number;
  resultsPerPage: number;
  loading: boolean;
  error: string | null;
  savedSearches: string[];
  searchHistory: string[];
  bookmarks: string[];
  viewMode: 'grid' | 'list';
  sortBy: 'relevance' | 'date_desc' | 'date_asc' | 'title';

  // Actions
  setQuery: (query: string) => void;
  setSearchType: (type: 'keyword' | 'semantic' | 'hybrid') => void;
  setFilters: (filters: SearchFilters) => void;
  setCurrentPage: (page: number) => void;
  setResultsPerPage: (count: number) => void;
  setViewMode: (mode: 'grid' | 'list') => void;
  setSortBy: (sort: 'relevance' | 'date_desc' | 'date_asc' | 'title') => void;
  addToHistory: (query: string) => void;
  addBookmark: (id: string) => void;
  removeBookmark: (id: string) => void;
  clearResults: () => void;
  resetFilters: () => void;
  performSearch: (query: string) => Promise<void>;
  getSuggestions: (query: string) => Promise<string[]>;
}

export const useSearchStore = create<SearchStore>()(
  persist(
    (set, get) => ({
      // Initial state
      query: '',
      searchType: 'hybrid',
      filters: {},
      results: [],
      totalResults: 0,
      currentPage: 1,
      resultsPerPage: 20,
      loading: false,
      error: null,
      savedSearches: [],
      searchHistory: [],
      bookmarks: [],
      viewMode: 'list',
      sortBy: 'relevance',

      // Actions
      setQuery: (query) => set({ query }),

      setSearchType: (searchType) => set({ searchType }),

      setFilters: (filters) => set({ filters }),

      setCurrentPage: (currentPage) => set({ currentPage }),

      setResultsPerPage: (resultsPerPage) => set({ resultsPerPage, currentPage: 1 }),

      setViewMode: (viewMode) => set({ viewMode }),

      setSortBy: (sortBy) => set({ sortBy }),

      addToHistory: (query) =>
        set((state) => {
          const history = [query, ...state.searchHistory.filter((q) => q !== query)];
          return { searchHistory: history.slice(0, 10) }; // Keep last 10 searches
        }),

      addBookmark: (id) =>
        set((state) => ({
          bookmarks: [...state.bookmarks, id]
        })),

      removeBookmark: (id) =>
        set((state) => ({
          bookmarks: state.bookmarks.filter(b => b !== id)
        })),

      clearResults: () =>
        set({
          results: [],
          totalResults: 0,
          currentPage: 1,
          query: ''
        }),

      resetFilters: () =>
        set({
          filters: {},
          currentPage: 1
        }),

      performSearch: async (query) => {
        const state = get();
        set({ loading: true, error: null, query });

        try {
          // Call real search service (which calls RAG through Gateway)
          const response = await searchService.search({
            query,
            searchType: state.searchType,
            filters: state.filters,
            page: state.currentPage,
            limit: state.resultsPerPage,
            sortBy: state.sortBy
          });

          // Use real results from API
          set({
            results: response.results,
            totalResults: response.totalResults,
            error: null
          });

          // Add to history
          get().addToHistory(query);

        } catch (error: any) {
          console.error('Search error:', error);
          set({
            error: error.message || 'Search failed. Please try again.',
            results: [],
            totalResults: 0
          });
        } finally {
          set({ loading: false });
        }
      },

      getSuggestions: async (query) => {
        // Mock suggestions for development (API not implemented yet)
        // TODO: Replace with actual API call when backend is ready
        if (!query || query.length < 2) return [];

        return [
          `${query} bangladesh law`,
          `${query} act`,
          `${query} section`,
          `${query} article`,
          `${query} constitution`
        ].slice(0, 5);
      }
    }),
    {
      name: 'search-storage',
      partialize: (state) => ({
        searchType: state.searchType,
        searchHistory: state.searchHistory,
        bookmarks: state.bookmarks,
        viewMode: state.viewMode,
        resultsPerPage: state.resultsPerPage,
        sortBy: state.sortBy
      }),
    }
  )
);