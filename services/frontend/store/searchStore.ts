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
          const response = await searchService.search({
            query,
            searchType: state.searchType,
            filters: state.filters,
            page: state.currentPage,
            limit: state.resultsPerPage,
            sortBy: state.sortBy
          });

          // Mock data for development
          const mockResults: SearchResult[] = [
            {
              id: '1',
              title: 'Bangladesh Constitution Article 32',
              lawNumber: 'CONST-32-1972',
              date: '1972-12-16',
              court: 'supreme',
              category: 'constitutional',
              snippet: 'No person shall be deprived of life or personal liberty save in accordance with law...',
              relevance: 0.95,
              url: '/laws/constitution/article-32',
              similarCount: 5
            },
            {
              id: '2',
              title: 'Criminal Procedure Code Section 144',
              lawNumber: 'CPC-144-1898',
              date: '1898-03-22',
              court: 'highCourt',
              category: 'criminal',
              snippet: 'Power to issue order in urgent cases of nuisance or apprehended danger...',
              relevance: 0.82,
              url: '/laws/cpc/section-144',
              similarCount: 3
            },
            {
              id: '3',
              title: 'Labour Act 2006 - Working Hours',
              lawNumber: 'LA-2006-CH5',
              date: '2006-10-11',
              court: 'tribunal',
              category: 'labor',
              snippet: 'No adult worker shall be required or allowed to work in an establishment for more than eight hours in a day...',
              relevance: 0.78,
              url: '/laws/labour/working-hours',
              similarCount: 8
            }
          ];

          set({
            results: mockResults,
            totalResults: 150,
            error: null
          });

          // Add to history
          get().addToHistory(query);

        } catch (error: any) {
          set({ error: error.message });
        } finally {
          set({ loading: false });
        }
      },

      getSuggestions: async (query) => {
        try {
          const suggestions = await searchService.getSuggestions(query);
          // Mock suggestions for development
          return [
            `${query} bangladesh`,
            `${query} law`,
            `${query} act`,
            `${query} section`,
            `${query} article`
          ].slice(0, 5);
        } catch (error) {
          return [];
        }
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