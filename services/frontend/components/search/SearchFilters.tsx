'use client';

import { useState } from 'react';
import { useSearchStore } from '@/store/searchStore';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ChevronDown, ChevronUp, RotateCcw } from 'lucide-react';

export function SearchFilters() {
  const t = useTranslations('search.filters');
  const { filters, setFilters, resetFilters } = useSearchStore();
  const [expandedSections, setExpandedSections] = useState({
    year: true,
    category: true,
    court: true,
    language: true
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleYearChange = (type: 'from' | 'to', value: string) => {
    setFilters({
      ...filters,
      yearRange: {
        ...filters.yearRange,
        [type]: value ? parseInt(value) : undefined
      }
    });
  };

  const categories = [
    'criminal', 'civil', 'constitutional', 'corporate',
    'family', 'labor', 'tax', 'environmental'
  ];

  const courtTypes = [
    'supreme', 'highCourt', 'district', 'magistrate', 'tribunal'
  ];

  const languages = ['english', 'bengali', 'both'];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-lg">{t('title')}</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={resetFilters}
          className="text-sm"
        >
          <RotateCcw className="h-3 w-3 mr-1" />
          {t('reset')}
        </Button>
      </div>

      {/* Year Range Filter */}
      <div className="border-b pb-4">
        <button
          onClick={() => toggleSection('year')}
          className="flex justify-between items-center w-full text-left font-medium mb-3"
        >
          {t('yearRange')}
          {expandedSections.year ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {expandedSections.year && (
          <div className="flex gap-2">
            <Input
              type="number"
              placeholder={t('from')}
              min="1947"
              max={new Date().getFullYear()}
              value={filters.yearRange?.from || ''}
              onChange={(e) => handleYearChange('from', e.target.value)}
              className="w-24"
            />
            <span className="self-center">-</span>
            <Input
              type="number"
              placeholder={t('to')}
              min="1947"
              max={new Date().getFullYear()}
              value={filters.yearRange?.to || ''}
              onChange={(e) => handleYearChange('to', e.target.value)}
              className="w-24"
            />
          </div>
        )}
      </div>

      {/* Category Filter */}
      <div className="border-b pb-4">
        <button
          onClick={() => toggleSection('category')}
          className="flex justify-between items-center w-full text-left font-medium mb-3"
        >
          {t('category')}
          {expandedSections.category ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {expandedSections.category && (
          <div className="space-y-2">
            {categories.map(category => (
              <label key={category} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.categories?.includes(category) || false}
                  onChange={(e) => {
                    const newCategories = e.target.checked
                      ? [...(filters.categories || []), category]
                      : (filters.categories || []).filter(c => c !== category);
                    setFilters({ ...filters, categories: newCategories });
                  }}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm">{t(`categories.${category}`)}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Court Type Filter */}
      <div className="border-b pb-4">
        <button
          onClick={() => toggleSection('court')}
          className="flex justify-between items-center w-full text-left font-medium mb-3"
        >
          {t('courtType')}
          {expandedSections.court ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {expandedSections.court && (
          <div className="space-y-2">
            {courtTypes.map(court => (
              <label key={court} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.courtTypes?.includes(court) || false}
                  onChange={(e) => {
                    const newCourtTypes = e.target.checked
                      ? [...(filters.courtTypes || []), court]
                      : (filters.courtTypes || []).filter(c => c !== court);
                    setFilters({ ...filters, courtTypes: newCourtTypes });
                  }}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm">{t(`courts.${court}`)}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Language Filter */}
      <div>
        <button
          onClick={() => toggleSection('language')}
          className="flex justify-between items-center w-full text-left font-medium mb-3"
        >
          {t('language')}
          {expandedSections.language ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {expandedSections.language && (
          <div className="space-y-2">
            {languages.map(lang => (
              <label key={lang} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="language"
                  value={lang}
                  checked={filters.language === lang}
                  onChange={() => setFilters({ ...filters, language: lang })}
                  className="text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm">{t(`languages.${lang}`)}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Active Filters Count */}
      {Object.values(filters).some(v => v && (Array.isArray(v) ? v.length > 0 : true)) && (
        <div className="pt-4 text-sm text-gray-600 dark:text-gray-400">
          {t('activeFilters', {
            count: Object.values(filters).filter(v => v && (Array.isArray(v) ? v.length > 0 : true)).length
          })}
        </div>
      )}
    </div>
  );
}