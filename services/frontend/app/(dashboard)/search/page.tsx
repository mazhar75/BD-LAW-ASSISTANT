'use client';

import { useState } from 'react';
import { SearchBar } from '@/components/search/SearchBar';
import { SearchResults } from '@/components/search/SearchResults';
import { SearchFilters } from '@/components/search/SearchFilters';
import { SearchTypeSelector } from '@/components/search/SearchTypeSelector';
import { Card } from '@/components/ui/Card';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/components/providers/ToastProvider';
import gatewayClient from '@/lib/api/client';

export default function SearchPage() {
  const { showToast } = useToast();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchType, setSearchType] = useState<'keyword' | 'semantic' | 'hybrid'>('hybrid');
  const [filters, setFilters] = useState({
    category: '',
    year: '',
    section: '',
  });

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      showToast({
        title: 'Empty Query',
        description: 'Please enter a search term',
        type: 'warning',
      });
      return;
    }

    setQuery(searchQuery);
    setIsLoading(true);

    try {
      // Call the RAG search API through gateway using authenticated client
      const response = await gatewayClient.post('/api/rag/search', {
        query: searchQuery,
        searchType: searchType,
        filters: filters,
        limit: 10,
      });

      const data = response.data;

      // Transform RAG service results to frontend format
      const transformedResults = data.results?.map((result: any, index: number) => ({
        id: result.chunk_id || index,
        title: result.title || 'Untitled Document',
        excerpt: result.content || result.text || '',
        category: result.metadata?.category || filters.category || '',
        year: result.metadata?.year || filters.year || '',
        section: result.section || result.metadata?.section_number || filters.section || '',
        relevance: result.score || 0,
      })) || [];

      setResults(transformedResults);

      showToast({
        title: 'Search Complete',
        description: `Found ${transformedResults.length} result(s)`,
        type: 'success',
      });
    } catch (error) {
      console.error('Search error:', error);
      showToast({
        title: 'Search Failed',
        description: error instanceof Error ? error.message : 'An error occurred while searching. Please try again.',
        type: 'error',
      });
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (newFilters: typeof filters) => {
    setFilters(newFilters);
    // Re-run search with new filters if there's a query
    if (query) {
      handleSearch(query);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold">Search Laws</h1>
        <p className="mt-2 text-muted-foreground">
          Search through Bangladesh legal documents and find relevant information
        </p>
      </div>

      {/* Search Type Selector */}
      <SearchTypeSelector
        value={searchType}
        onChange={setSearchType}
      />

      {/* Search Bar */}
      <Card className="p-6">
        <SearchBar
          onSearch={handleSearch}
          initialValue={query}
        />
      </Card>

      {/* Filters */}
      <SearchFilters
        filters={filters}
        onChange={handleFilterChange}
      />

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {/* Results */}
      {!isLoading && query && (
        <SearchResults
          results={results}
          query={query}
          searchType={searchType}
        />
      )}

      {/* Empty State */}
      {!isLoading && !query && (
        <Card className="p-12">
          <div className="text-center">
            <div className="mx-auto h-12 w-12 text-muted-foreground mb-4">
              <svg
                className="w-full h-full"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium mb-2">Start Your Search</h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              Enter keywords, legal terms, or questions to search through Bangladesh legal documents
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
