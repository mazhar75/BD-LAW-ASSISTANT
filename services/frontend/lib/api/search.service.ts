import gatewayClient from './client';
import { SearchRequest, SearchResponse, SavedSearch, SearchResult } from '@/types/search.types';
import { ApiError } from '@/types/errors';

class SearchService {
  async search(request: SearchRequest): Promise<SearchResponse> {
    try {
      // Map frontend request to RAG service format
      const ragRequest = {
        query: request.query,
        language: request.filters?.language || 'en',
        top_k: request.limit || 20,
        threshold: 0.5,
        filters: {
          categories: request.filters?.categories,
          yearRange: request.filters?.yearRange
        }
      };

      const response = await gatewayClient.post('/api/rag/search', ragRequest);

      // Transform RAG response to frontend format
      const ragData = response.data;
      const results: SearchResult[] = (ragData.results || []).map((item: any, index: number) => ({
        id: `${item.chunk_id || index}`,
        title: item.title || 'Untitled Law',
        lawNumber: `ACT-${item.act_number || 0}`,
        date: item.metadata?.year ? `${item.metadata.year}-01-01` : '1972-01-01',
        court: 'supreme',
        category: item.metadata?.category || 'constitutional',
        snippet: item.content?.substring(0, 200) || '',
        fullText: item.content,
        relevance: item.score || 0,
        url: `/laws/${item.act_number || 0}/${item.chunk_id || 0}`,
        similarCount: 0
      }));

      return {
        results,
        totalResults: ragData.total_results || results.length,
        page: request.page || 1,
        totalPages: Math.ceil((ragData.total_results || results.length) / (request.limit || 20)),
        executionTime: ragData.search_time_ms || 0
      };
    } catch (error: any) {
      console.error('Search failed:', error);
      throw new Error(error.response?.data?.error || error.message || 'Search failed');
    }
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