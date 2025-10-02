import gatewayClient from './client';
import { SearchRequest, SearchResponse, SavedSearch } from '@/types/search.types';
import { ApiError } from '@/types/errors';

class SearchService {
  async search(request: SearchRequest): Promise<SearchResponse> {
    const response = await gatewayClient.post('/api/rag/search', request);
    return response.data;
  }

  async getSuggestions(query: string): Promise<string[]> {
    try {
      const response = await gatewayClient.get('/api/rag/suggestions', {
        params: { query }
      });
      return response.data.suggestions || [];
    } catch (error: unknown) {
      console.error('Failed to get suggestions:', (error as ApiError).message);
      return [];
    }
  }

  async getSimilar(lawId: string): Promise<SearchResponse> {
    const response = await gatewayClient.get(`/api/rag/similar/${lawId}`);
    return response.data;
  }

  async getSearchHistory(): Promise<string[]> {
    try {
      const response = await gatewayClient.get('/api/user/search-history');
      return response.data.history || [];
    } catch (error: unknown) {
      console.error('Failed to get search history:', (error as ApiError).message);
      return [];
    }
  }

  async getSavedSearches(): Promise<SavedSearch[]> {
    try {
      const response = await gatewayClient.get('/api/user/saved-searches');
      return response.data.searches || [];
    } catch (error: unknown) {
      console.error('Failed to get saved searches:', (error as ApiError).message);
      return [];
    }
  }

  async saveSearch(name: string, query: string, filters: Record<string, unknown>): Promise<void> {
    await gatewayClient.post('/api/user/saved-searches', {
      name,
      query,
      filters
    });
  }

  async deleteSavedSearch(id: string): Promise<void> {
    await gatewayClient.delete(`/api/user/saved-searches/${id}`);
  }

  async exportResults(resultIds: string[], format: 'pdf' | 'excel' | 'json'): Promise<Blob | object> {
    const response = await gatewayClient.post('/api/rag/export', {
      resultIds,
      format
    }, {
      responseType: format === 'json' ? 'json' : 'blob'
    });
    return response.data;
  }
}

export const searchService = new SearchService();