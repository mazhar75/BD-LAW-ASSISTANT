'use client';

import { Card } from '@/components/ui/Card';
import { FileText, Scale, Calendar, BookOpen, ChevronRight, Hash } from 'lucide-react';
import { BookmarkButton } from '@/components/bookmarks/BookmarkButton';

interface SearchResultsProps {
  results: any[];
  query: string;
  searchType?: string;
}

export function SearchResults({ results, query, searchType }: SearchResultsProps) {
  if (results.length === 0) {
    return (
      <Card className="p-12 bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-200 mb-4">
            <FileText className="h-8 w-8 text-slate-500" />
          </div>
          <h3 className="text-xl font-semibold mb-2 text-slate-900">No Results Found</h3>
          <p className="text-slate-600 max-w-md mx-auto">
            No documents found for <span className="font-medium text-slate-900">"{query}"</span>.
            Try different keywords or adjust your filters.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Results Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 pb-4 border-b border-slate-200">
        <div>
          <p className="text-sm text-slate-600">
            Found <span className="font-semibold text-slate-900">{results.length}</span> result{results.length !== 1 ? 's' : ''} for
          </p>
          <p className="text-lg font-medium text-slate-900 mt-0.5">"{query}"</p>
        </div>
        {searchType && (
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 text-blue-700 rounded-lg text-sm font-medium">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            {searchType} search
          </div>
        )}
      </div>

      {/* Results List */}
      <div className="space-y-4">
        {results.map((result, index) => (
          <Card
            key={index}
            className="group relative overflow-hidden border border-slate-200 hover:border-blue-300 hover:shadow-lg transition-all duration-300 bg-white"
          >
            {/* Gradient Accent Bar */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>

            <div className="p-6">
              {/* Header */}
              <div className="flex justify-between items-start gap-4 mb-4">
                <div className="flex-1">
                  <div className="flex items-start gap-3">
                    <div className="mt-1">
                      <Scale className="h-5 w-5 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-slate-900 leading-tight group-hover:text-blue-600 transition-colors">
                        {result.title}
                      </h3>
                      {result.chunk_id && (
                        <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                          <Hash className="h-3 w-3" />
                          {result.chunk_id}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
                <BookmarkButton
                  item={{
                    itemId: String(result.id || `search-${index}`),
                    bookmarkType: 'search_result',
                    title: result.title,
                    excerpt: result.excerpt || result.snippet || '',
                    category: result.category,
                    section: result.section,
                    year: result.year,
                    url: result.url || `/laws/${result.id}`
                  }}
                  size="sm"
                />
              </div>

              {/* Excerpt */}
              <div className="mb-4 pl-8">
                <p className="text-sm text-slate-700 leading-relaxed line-clamp-3">
                  {result.excerpt || result.text || 'No excerpt available'}
                </p>
              </div>

              {/* Metadata Tags */}
              <div className="flex flex-wrap gap-2 pl-8">
                {result.category && (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-purple-50 border border-purple-200 text-purple-700 rounded-full text-xs font-medium">
                    <BookOpen className="h-3 w-3" />
                    {result.category}
                  </div>
                )}
                {result.year && (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-full text-xs font-medium">
                    <Calendar className="h-3 w-3" />
                    {result.year}
                  </div>
                )}
                {result.section && (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 border border-amber-200 text-amber-700 rounded-full text-xs font-medium">
                    <FileText className="h-3 w-3" />
                    {result.section}
                  </div>
                )}
              </div>

              {/* View Details Link */}
              <div className="mt-4 pl-8">
                <button className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium group/link">
                  View full text
                  <ChevronRight className="h-4 w-4 transition-transform group-hover/link:translate-x-0.5" />
                </button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
