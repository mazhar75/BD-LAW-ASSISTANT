'use client';

import { Button } from '@/components/ui/Button';
import { MessageSquare, Trash2 } from 'lucide-react';
import { Conversation } from '@/types/chat.types';
import { useChatStore } from '@/store/chatStore';

interface ConversationHistoryProps {
  conversations: Conversation[];
  activeId?: string;
  onSelect: (id: string) => void;
}

export function ConversationHistory({ conversations, activeId, onSelect }: ConversationHistoryProps) {
  const { deleteConversation } = useChatStore();

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    deleteConversation(id);
  };

  const groupByDate = (conversations: Conversation[]) => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);

    const groups: { [key: string]: Conversation[] } = {
      Today: [],
      Yesterday: [],
      'This Week': [],
      Older: []
    };

    conversations.forEach(conv => {
      const date = new Date(conv.updatedAt);
      if (date.toDateString() === today.toDateString()) {
        groups['Today'].push(conv);
      } else if (date.toDateString() === yesterday.toDateString()) {
        groups['Yesterday'].push(conv);
      } else if (date > weekAgo) {
        groups['This Week'].push(conv);
      } else {
        groups['Older'].push(conv);
      }
    });

    return groups;
  };

  const grouped = groupByDate(conversations);

  return (
    <div className="flex-1 overflow-y-auto space-y-4">
      {Object.entries(grouped).map(([period, convs]) => {
        if (convs.length === 0) return null;

        return (
          <div key={period}>
            <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
              {period}
            </h4>
            <div className="space-y-1">
              {convs.map(conversation => (
                <button
                  key={conversation.id}
                  onClick={() => onSelect(conversation.id)}
                  className={`
                    w-full text-left p-3 rounded-lg transition-colors group
                    ${activeId === conversation.id
                      ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                    }
                  `}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <MessageSquare className="h-3 w-3 text-gray-400" />
                        <span className="text-sm font-medium truncate">
                          {conversation.title}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 truncate">
                        {conversation.messages[conversation.messages.length - 1]?.content || 'Empty conversation'}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => handleDelete(e, conversation.id)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </button>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}