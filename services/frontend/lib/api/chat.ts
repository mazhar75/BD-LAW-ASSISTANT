import gatewayClient, { handleApiError } from './client';
import { ChatRequest, ChatResponse, Conversation } from '@/types/chat';

export const chatApi = {
  // Send a chat/question
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    try {
      const response = await gatewayClient.post<ChatResponse>('/api/rag/ask', request);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Get conversation history
  getConversations: async (limit = 20): Promise<Conversation[]> => {
    try {
      const response = await gatewayClient.get<Conversation[]>(
        `/api/user/conversations?limit=${limit}`
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Get specific conversation
  getConversation: async (conversationId: string): Promise<Conversation> => {
    try {
      const response = await gatewayClient.get<Conversation>(
        `/api/user/conversations/${conversationId}`
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Create new conversation
  createConversation: async (title?: string): Promise<Conversation> => {
    try {
      const response = await gatewayClient.post<Conversation>(
        '/api/user/conversations',
        { title: title || 'New Conversation' }
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Delete conversation
  deleteConversation: async (conversationId: string): Promise<{ message: string }> => {
    try {
      const response = await gatewayClient.delete(
        `/api/user/conversations/${conversationId}`
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Export conversation
  exportConversation: async (
    conversationId: string,
    format: 'pdf' | 'md' | 'json'
  ): Promise<Blob> => {
    try {
      const response = await gatewayClient.get(
        `/api/user/conversations/${conversationId}/export`,
        {
          params: { format },
          responseType: 'blob',
        }
      );
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Submit feedback for a message
  submitFeedback: async (
    messageId: string,
    feedback: 'helpful' | 'not_helpful',
    comment?: string
  ): Promise<{ message: string }> => {
    try {
      const response = await gatewayClient.post('/api/rag/feedback', {
        messageId,
        feedback,
        comment,
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
};