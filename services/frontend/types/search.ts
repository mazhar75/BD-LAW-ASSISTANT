export interface SearchRequest {
  query: string;
  searchType?: 'keyword' | 'semantic' | 'hybrid';
  filters?: SearchFilters;
  page?: number;
  limit?: number;
}

export interface SearchFilters {
  year?: {
    start?: number;
    end?: number;
  };
  categories?: string[];
  courts?: string[];
  language?: 'en' | 'bn' | 'all';
}

export interface SearchResult {
  id: string;
  title: string;
  snippet: string;
  content?: string;
  relevanceScore: number;
  metadata: {
    year?: number;
    category?: string;
    court?: string;
    language?: string;
    url?: string;
  };
  highlights?: string[];
}

export interface SearchResponse {
  results: SearchResult[];
  totalResults: number;
  page: number;
  totalPages: number;
  queryId: string;
  processingTime: number;
}

export interface SimilarLawsResponse {
  lawId: string;
  similarLaws: SearchResult[];
}

export interface SavedSearch {
  id: string;
  name: string;
  query: string;
  filters: SearchFilters;
  createdAt: string;
  lastUsed?: string;
}