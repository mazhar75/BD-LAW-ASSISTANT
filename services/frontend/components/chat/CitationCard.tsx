'use client';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ExternalLink, FileText } from 'lucide-react';
import { Citation } from '@/types/chat.types';

interface CitationCardProps {
  citation: Citation;
}

export function CitationCard({ citation }: CitationCardProps) {
  return (
    <Card className="p-3 bg-gray-50 dark:bg-gray-800/50">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <FileText className="h-4 w-4 text-gray-500" />
            <span className="font-medium text-sm">{citation.title}</span>
          </div>
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
            {citation.lawNumber} • {citation.year}
          </p>
          <p className="text-sm text-gray-700 dark:text-gray-300">
            {citation.snippet}
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => window.open(citation.url, '_blank')}
        >
          <ExternalLink className="h-3 w-3" />
        </Button>
      </div>
    </Card>
  );
}