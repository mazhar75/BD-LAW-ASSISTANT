import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Conversation, Message, ChatRequest, ChatResponse } from '@/types/chat';
import { chatApi } from '@/lib/api';

interface ChatStore {
  // State
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  suggestedQuestions: string[];

  // Actions
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (conversation: Conversation | null) => void;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSuggestedQuestions: (questions: string[]) => void;

  // API Actions
  loadConversations: () => Promise<void>;
  loadConversation: (conversationId: string) => Promise<void>;
  createConversation: (title?: string) => Promise<Conversation>;
  deleteConversation: (conversationId: string) => Promise<void>;
  sendMessage: (message: string, conversationId?: string) => Promise<ChatResponse>;
  exportConversation: (conversationId: string, format: 'pdf' | 'md' | 'json') => Promise<void>;
  submitFeedback: (messageId: string, feedback: 'helpful' | 'not_helpful', comment?: string) => Promise<void>;
  clearConversation: () => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      // Initial state
      conversations: [],
      currentConversation: null,
      messages: [],
      isLoading: false,
      error: null,
      suggestedQuestions: [],

      // Actions
      setConversations: (conversations) => set({ conversations }),

      setCurrentConversation: (conversation) =>
        set({
          currentConversation: conversation,
          messages: conversation?.messages || [],
        }),

      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),

      setMessages: (messages) => set({ messages }),

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      setSuggestedQuestions: (suggestedQuestions) => set({ suggestedQuestions }),

      // API Actions
      loadConversations: async () => {
        try {
          set({ isLoading: true, error: null });
          const conversations = await chatApi.getConversations();
          set({ conversations });
        } catch (error: any) {
          set({ error: error.message });
        } finally {
          set({ isLoading: false });
        }
      },

      loadConversation: async (conversationId) => {
        try {
          set({ isLoading: true, error: null });
          const conversation = await chatApi.getConversation(conversationId);
          set({
            currentConversation: conversation,
            messages: conversation.messages,
          });
        } catch (error: any) {
          set({ error: error.message });
        } finally {
          set({ isLoading: false });
        }
      },

      createConversation: async (title) => {
        try {
          set({ isLoading: true, error: null });
          const conversation = await chatApi.createConversation(title);
          set((state) => ({
            conversations: [conversation, ...state.conversations],
            currentConversation: conversation,
            messages: [],
          }));
          return conversation;
        } catch (error: any) {
          set({ error: error.message });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      deleteConversation: async (conversationId) => {
        try {
          await chatApi.deleteConversation(conversationId);
          set((state) => ({
            conversations: state.conversations.filter((c) => c.id !== conversationId),
            currentConversation:
              state.currentConversation?.id === conversationId ? null : state.currentConversation,
            messages:
              state.currentConversation?.id === conversationId ? [] : state.messages,
          }));
        } catch (error: any) {
          set({ error: error.message });
          throw error;
        }
      },

      sendMessage: async (message, conversationId) => {
        const state = get();
        let convId = conversationId || state.currentConversation?.id;

        // Create a new conversation if none exists
        if (!convId) {
          const newConv = await get().createConversation();
          convId = newConv.id;
        }

        // Add user message immediately
        const userMessage: Message = {
          id: Date.now().toString(),
          content: message,
          role: 'user',
          timestamp: new Date().toISOString(),
        };
        get().addMessage(userMessage);

        try {
          set({ isLoading: true, error: null });
          const response = await chatApi.sendMessage({
            message,
            conversationId: convId,
          });

          // Add assistant message
          get().addMessage(response.message);

          // Update suggested questions
          if (response.suggestedQuestions) {
            set({ suggestedQuestions: response.suggestedQuestions });
          }

          return response;
        } catch (error: any) {
          set({ error: error.message });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      exportConversation: async (conversationId, format) => {
        try {
          const blob = await chatApi.exportConversation(conversationId, format);

          // Create download link
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `conversation-${conversationId}.${format}`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        } catch (error: any) {
          set({ error: error.message });
          throw error;
        }
      },

      submitFeedback: async (messageId, feedback, comment) => {
        try {
          await chatApi.submitFeedback(messageId, feedback, comment);

          // Update message feedback in state
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === messageId ? { ...msg, feedback } : msg
            ),
          }));
        } catch (error: any) {
          set({ error: error.message });
          throw error;
        }
      },

      clearConversation: () =>
        set({
          currentConversation: null,
          messages: [],
          suggestedQuestions: [],
          error: null,
        }),
    }),
    {
      name: 'chat-storage',
      partialize: (state) => ({
        conversations: state.conversations.slice(0, 10), // Keep last 10 conversations
        suggestedQuestions: state.suggestedQuestions,
      }),
    }
  )
);