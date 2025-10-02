import gatewayClient from './client';
import { ChatRequest, ChatResponse, Conversation } from '@/types/chat.types';

class ChatService {
  async getConversations(): Promise<Conversation[]> {
    const response = await gatewayClient.get('/api/chat/conversations');
    return response.data;
  }

  async getConversation(id: string): Promise<Conversation> {
    const response = await gatewayClient.get(`/api/chat/conversations/${id}`);
    return response.data;
  }

  async createConversation(title?: string): Promise<Conversation> {
    const response = await gatewayClient.post('/api/chat/conversations', { title });
    return response.data;
  }

  async deleteConversation(id: string): Promise<void> {
    await gatewayClient.delete(`/api/chat/conversations/${id}`);
  }

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await gatewayClient.post('/api/rag/ask', request);
    return response.data;
  }

  async exportConversation(id: string, format: 'pdf' | 'md' | 'json'): Promise<Blob> {
    const response = await gatewayClient.get(`/api/chat/conversations/${id}/export`, {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
  }

  async submitFeedback(messageId: string, feedback: 'helpful' | 'not_helpful', comment?: string): Promise<void> {
    await gatewayClient.post('/api/rag/feedback', {
      messageId,
      feedback,
      comment
    });
  }
}

export const chatService = new ChatService();