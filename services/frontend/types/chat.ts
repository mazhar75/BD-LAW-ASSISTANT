export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  sources?: Source[];
  feedback?: 'helpful' | 'not_helpful';
}

export interface Source {
  id: string;
  title: string;
  snippet: string;
  relevanceScore?: number;
  metadata?: {
    year?: number;
    category?: string;
    url?: string;
  };
}

export interface ChatRequest {
  message: string;
  conversationId?: string;
  context?: string[];
  searchType?: 'keyword' | 'semantic' | 'hybrid';
}

export interface ChatResponse {
  message: Message;
  conversationId: string;
  sources: Source[];
  suggestedQuestions?: string[];
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

export interface ChatState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  isLoading: boolean;
  error: string | null;
}