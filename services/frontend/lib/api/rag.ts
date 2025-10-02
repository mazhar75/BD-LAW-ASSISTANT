import gatewayClient, { handleApiError } from './client';

export interface QueryRequest {
  query: string;
  context?: Array<{
    role: string;
    content: string;
  }>;
}

export interface QueryResponse {
  answer: string;
  sources?: Array<{
    title: string;
    content: string;
    relevance?: number;
  }>;
  confidence?: number;
}

export interface DocumentUploadResponse {
  message: string;
  documentId?: string;
}

export const ragApi = {
  // Query the RAG system
  query: async (request: QueryRequest): Promise<QueryResponse> => {
    try {
      const response = await gatewayClient.post<QueryResponse>(
        '/api/rag/query',
        request
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Upload a document to the RAG system
  uploadDocument: async (file: File): Promise<DocumentUploadResponse> => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await gatewayClient.post<DocumentUploadResponse>(
        '/api/rag/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Get document status
  getDocumentStatus: async (documentId: string): Promise<any> => {
    try {
      const response = await gatewayClient.get(`/api/rag/document/${documentId}`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Delete a document
  deleteDocument: async (documentId: string): Promise<{ message: string }> => {
    try {
      const response = await gatewayClient.delete(`/api/rag/document/${documentId}`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Search documents
  searchDocuments: async (query: string, limit: number = 10): Promise<any[]> => {
    try {
      const response = await gatewayClient.get('/api/rag/search', {
        params: {
          query,
          limit,
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
};