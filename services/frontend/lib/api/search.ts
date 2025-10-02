import gatewayClient, { handleApiError } from './client';
import { SearchRequest, SearchResponse, SimilarLawsResponse } from '@/types/search';

export const searchApi = {
  // Search laws
  search: async (request: SearchRequest): Promise<SearchResponse> => {
    try {
      const response = await gatewayClient.post<SearchResponse>(
        '/api/rag/search',
        request
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Get similar laws
  getSimilarLaws: async (lawId: string | number): Promise<SimilarLawsResponse> => {
    try {
      const response = await gatewayClient.get<SimilarLawsResponse>(
        `/api/rag/similar/${lawId}`
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Submit feedback for search results
  submitFeedback: async (
    queryId: string,
    resultId: string,
    feedback: 'helpful' | 'not_helpful',
    comment?: string
  ): Promise<{ message: string }> => {
    try {
      const response = await gatewayClient.post('/api/rag/feedback', {
        queryId,
        resultId,
        feedback,
        comment,
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Export search results
  exportResults: async (
    format: 'pdf' | 'excel' | 'json',
    resultIds: string[]
  ): Promise<Blob> => {
    try {
      const response = await gatewayClient.post(
        '/api/rag/export',
        {
          format,
          resultIds,
        },
        {
          responseType: 'blob',
        }
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Save search query
  saveSearch: async (
    query: string,
    filters: Record<string, unknown>,
    name: string
  ): Promise<{ id: string; message: string }> => {
    try {
      const response = await gatewayClient.post('/api/user/saved-searches', {
        query,
        filters,
        name,
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Get saved searches
  getSavedSearches: async (): Promise<
    Array<{ id: string; name: string; query: string; filters: Record<string, unknown>; createdAt: string }>
  > => {
    try {
      const response = await gatewayClient.get('/api/user/saved-searches');
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Delete saved search
  deleteSavedSearch: async (searchId: string): Promise<{ message: string }> => {
    try {
      const response = await gatewayClient.delete(
        `/api/user/saved-searches/${searchId}`
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
};