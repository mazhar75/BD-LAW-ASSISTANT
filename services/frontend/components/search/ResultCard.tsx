'use client';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Bookmark, ExternalLink, FileText, Star, Calendar, Building, Hash } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useSearchStore } from '@/store/searchStore';
import { SearchResult } from '@/types/search.types';
import { useState } from 'react';

interface ResultCardProps {
  result: SearchResult;
  viewMode: 'grid' | 'list';
  selected: boolean;
  onSelect: () => void;
}

export function ResultCard({ result, viewMode, selected, onSelect }: ResultCardProps) {
  const t = useTranslations('search.results');
  const { addBookmark, removeBookmark, bookmarks } = useSearchStore();
  const [expanded, setExpanded] = useState(false);

  const isBookmarked = bookmarks.includes(result.id);

  const handleBookmarkToggle = () => {
    if (isBookmarked) {
      removeBookmark(result.id);
    } else {
      addBookmark(result.id);
    }
  };

  const highlightText = (text: string) => {
    // Simple highlight simulation - in real app, this would highlight search terms
    const parts = text.split(/(\b\w+\b)/g);
    return parts.map((part, i) => {
      if (i % 2 === 1 && Math.random() > 0.7) {
        return <mark key={i} className="bg-yellow-200 dark:bg-yellow-800 px-0.5">{part}</mark>;
      }
      return part;
    });
  };

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const relevanceColor = result.relevance >= 0.8 ? 'text-green-600' :
                         result.relevance >= 0.6 ? 'text-yellow-600' :
                         'text-gray-600';

  return (
    <Card className={`
      ${selected ? 'ring-2 ring-blue-500' : ''}
      hover:shadow-lg transition-shadow duration-200
      ${viewMode === 'list' ? 'p-4' : 'p-5'}
    `}>
      <div className="flex gap-3">
        {/* Checkbox */}
        <div className="flex-shrink-0 pt-1">
          <input
            type="checkbox"
            checked={selected}
            onChange={onSelect}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title */}
          <h3 className="font-semibold text-lg mb-2 flex items-start justify-between gap-2">
            <span className="flex-1">
              {highlightText(result.title)}
            </span>
            {/* Relevance Score */}
            <span className={`text-sm font-normal ${relevanceColor} flex items-center gap-1`}>
              <Star className="h-3 w-3" />
              {(result.relevance * 100).toFixed(0)}%
            </span>
          </h3>

          {/* Metadata */}
          <div className="flex flex-wrap gap-3 text-xs text-gray-600 dark:text-gray-400 mb-3">
            <span className="flex items-center gap-1">
              <FileText className="h-3 w-3" />
              {result.lawNumber}
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {new Date(result.date).getFullYear()}
            </span>
            <span className="flex items-center gap-1">
              <Building className="h-3 w-3" />
              {t(`courts.${result.court}`)}
            </span>
            <span className="flex items-center gap-1">
              <Hash className="h-3 w-3" />
              {t(`categories.${result.category}`)}
            </span>
          </div>

          {/* Snippet */}
          <div className="text-sm text-gray-700 dark:text-gray-300 mb-3 leading-relaxed">
            {expanded ? (
              <div>
                {highlightText(result.snippet)}
                {result.fullText && (
                  <div className="mt-2 pt-2 border-t">
                    {result.fullText}
                  </div>
                )}
              </div>
            ) : (
              highlightText(truncateText(result.snippet, viewMode === 'grid' ? 150 : 250))
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? t('showLess') : t('showMore')}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleBookmarkToggle}
            >
              <Bookmark
                className={`h-3 w-3 mr-1 ${isBookmarked ? 'fill-current' : ''}`}
              />
              {isBookmarked ? t('bookmarked') : t('bookmark')}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(result.url, '_blank')}
            >
              <ExternalLink className="h-3 w-3 mr-1" />
              {t('view')}
            </Button>
          </div>

          {/* Similar Laws Link */}
          {result.similarCount > 0 && (
            <div className="mt-3 pt-3 border-t">
              <Button
                variant="ghost"
                size="sm"
                className="text-blue-600 hover:text-blue-700"
              >
                {t('similarLaws', { count: result.similarCount })}
              </Button>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}