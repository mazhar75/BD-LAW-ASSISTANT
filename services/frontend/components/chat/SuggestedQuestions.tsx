'use client';

import { Button } from '@/components/ui/Button';
import { HelpCircle } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';

const SUGGESTED_QUESTIONS = [
  "What are my fundamental rights under the Bangladesh Constitution?",
  "Explain the Labour Act 2006 working hours regulations",
  "What is the procedure for filing a criminal complaint?",
  "What are the grounds for divorce under family law?",
  "How does the tax exemption work for small businesses?",
  "What are the environmental protection laws in Bangladesh?"
];

export function SuggestedQuestions() {
  const { sendMessage } = useChatStore();

  const handleQuestionClick = (question: string) => {
    sendMessage(question);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
      {SUGGESTED_QUESTIONS.map((question, index) => (
        <Button
          key={index}
          variant="outline"
          className="justify-start text-left h-auto py-3 px-4"
          onClick={() => handleQuestionClick(question)}
        >
          <HelpCircle className="h-4 w-4 mr-2 flex-shrink-0" />
          <span className="text-sm">{question}</span>
        </Button>
      ))}
    </div>
  );
}