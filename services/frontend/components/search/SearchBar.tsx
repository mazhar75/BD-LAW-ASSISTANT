'use client';

import { useState, useEffect, useRef } from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Search, X, Clock, Star } from 'lucide-react';
import { useSearchStore } from '@/store/searchStore';
import { useDebounce } from '@/hooks/useDebounce';

interface SearchBarProps {
  onSearch: (query: string) => void;
  initialValue?: string;
}

export function SearchBar({ onSearch, initialValue = '' }: SearchBarProps) {
  const [query, setQuery] = useState(initialValue);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const debouncedQuery = useDebounce(query, 300);
  const searchRef = useRef<HTMLDivElement>(null);

  const { searchHistory, savedSearches, addToHistory, getSuggestions } = useSearchStore();

  useEffect(() => {
    setQuery(initialValue);
  }, [initialValue]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (debouncedQuery && debouncedQuery.length > 2) {
        const newSuggestions = await getSuggestions(debouncedQuery);
        setSuggestions(newSuggestions);
      } else {
        setSuggestions([]);
      }
    };

    fetchSuggestions();
  }, [debouncedQuery, getSuggestions]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      addToHistory(query.trim());
      onSearch(query.trim());
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    addToHistory(suggestion);
    onSearch(suggestion);
    setShowSuggestions(false);
  };

  const handleClear = () => {
    setQuery('');
    setShowSuggestions(false);
  };

  const combinedSuggestions = [
    ...savedSearches.map(s => ({ text: s, type: 'saved' })),
    ...searchHistory.slice(0, 5).map(h => ({ text: h, type: 'history' })),
    ...suggestions.map(s => ({ text: s, type: 'suggestion' }))
  ];

  return (
    <div ref={searchRef} className="relative">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            placeholder="Search for laws, acts, sections, or legal topics..."
            className="pr-10"
          />
          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <Button type="submit" disabled={!query.trim()}>
          <Search className="h-4 w-4 mr-2" />
          Search
        </Button>
      </form>

      {/* Suggestions Dropdown */}
      {showSuggestions && combinedSuggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 max-h-96 overflow-y-auto">
          {combinedSuggestions.map((item, index) => (
            <button
              key={`${item.type}-${index}`}
              onClick={() => handleSuggestionClick(item.text)}
              className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-3 transition-colors"
            >
              {item.type === 'saved' && <Star className="h-4 w-4 text-yellow-500" />}
              {item.type === 'history' && <Clock className="h-4 w-4 text-gray-400" />}
              {item.type === 'suggestion' && <Search className="h-4 w-4 text-blue-500" />}
              <span className="flex-1 truncate">{item.text}</span>
              <span className="text-xs text-gray-500">
                {item.type === 'saved' && 'Saved'}
                {item.type === 'history' && 'Recent'}
                {item.type === 'suggestion' && 'Suggested'}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}