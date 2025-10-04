'use client';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { RotateCcw } from 'lucide-react';

interface SearchFiltersProps {
  filters: {
    category?: string;
    year?: string;
    section?: string;
  };
  onChange: (filters: any) => void;
}

export function SearchFilters({ filters, onChange }: SearchFiltersProps) {
  const handleReset = () => {
    onChange({
      category: '',
      year: '',
      section: '',
    });
  };

  const handleChange = (key: string, value: string) => {
    onChange({
      ...filters,
      [key]: value,
    });
  };

  const categories = [
    { value: '', label: 'All Categories' },
    { value: 'criminal', label: 'Criminal' },
    { value: 'civil', label: 'Civil' },
    { value: 'constitutional', label: 'Constitutional' },
    { value: 'corporate', label: 'Corporate' },
    { value: 'family', label: 'Family' },
    { value: 'labor', label: 'Labor' },
    { value: 'tax', label: 'Tax' },
    { value: 'environmental', label: 'Environmental' }
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold">Filters</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleReset}
          className="text-sm"
        >
          <RotateCcw className="h-3 w-3 mr-1" />
          Reset
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Category Filter */}
        <div>
          <label className="block text-sm font-medium mb-2">Category</label>
          <select
            value={filters.category || ''}
            onChange={(e) => handleChange('category', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {categories.map(cat => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
        </div>

        {/* Year Filter */}
        <div>
          <label className="block text-sm font-medium mb-2">Year</label>
          <Input
            type="number"
            placeholder="e.g., 2020"
            value={filters.year || ''}
            onChange={(e) => handleChange('year', e.target.value)}
            min="1947"
            max={new Date().getFullYear()}
          />
        </div>

        {/* Section Filter */}
        <div>
          <label className="block text-sm font-medium mb-2">Section</label>
          <Input
            type="text"
            placeholder="e.g., Section 302"
            value={filters.section || ''}
            onChange={(e) => handleChange('section', e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}
