export interface SearchResult {
  id: string;
  title: string;
  lawNumber: string;
  date: string;
  court: string;
  category: string;
  snippet: string;
  fullText?: string;
  relevance: number;
  url: string;
  similarCount: number;
}

export interface SearchFilters {
  yearRange?: {
    from?: number;
    to?: number;
  };
  categories?: string[];
  courtTypes?: string[];
  language?: string;
}

export interface SearchRequest {
  query: string;
  searchType: 'keyword' | 'semantic' | 'hybrid';
  filters?: SearchFilters;
  page?: number;
  limit?: number;
  sortBy?: 'relevance' | 'date_desc' | 'date_asc' | 'title';
}

export interface SearchResponse {
  results: SearchResult[];
  totalResults: number;
  page: number;
  totalPages: number;
  executionTime: number;
}

export interface SearchSuggestion {
  text: string;
  type: 'history' | 'saved' | 'suggestion';
}

export interface SavedSearch {
  id: string;
  name: string;
  query: string;
  filters: SearchFilters;
  createdAt: string;
}