export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: Citation[];
}

export interface Citation {
  title: string;
  lawNumber: string;
  year: string;
  snippet: string;
  url: string;
  relevance: number;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

export interface ChatRequest {
  message: string;
  conversationId?: string;
  context?: any;
}

export interface ChatResponse {
  message: Message;
  citations: Citation[];
  suggestedQuestions?: string[];
}