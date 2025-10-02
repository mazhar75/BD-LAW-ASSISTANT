'use client';

import { useSearchStore } from '@/store/searchStore';
import { ResultCard } from './ResultCard';
import { Pagination } from '@/components/ui/Pagination';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/Button';
import { Download, SortAsc } from 'lucide-react';
import { useState } from 'react';
import { ExportDialog } from './ExportDialog';

export function SearchResults() {
  const t = useTranslations('search.results');
  const {
    results,
    totalResults,
    currentPage,
    resultsPerPage,
    viewMode,
    sortBy,
    setSortBy,
    setCurrentPage,
    setResultsPerPage
  } = useSearchStore();

  const [showExportDialog, setShowExportDialog] = useState(false);
  const [selectedResults, setSelectedResults] = useState<string[]>([]);

  const sortOptions = [
    { value: 'relevance', label: t('sort.relevance') },
    { value: 'date_desc', label: t('sort.dateDesc') },
    { value: 'date_asc', label: t('sort.dateAsc') },
    { value: 'title', label: t('sort.title') }
  ];

  const handleSelectResult = (id: string) => {
    setSelectedResults(prev =>
      prev.includes(id)
        ? prev.filter(r => r !== id)
        : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedResults.length === results.length) {
      setSelectedResults([]);
    } else {
      setSelectedResults(results.map(r => r.id));
    }
  };

  const totalPages = Math.ceil(totalResults / resultsPerPage);

  return (
    <div>
      {/* Results Header */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {t('showing', {
              start: (currentPage - 1) * resultsPerPage + 1,
              end: Math.min(currentPage * resultsPerPage, totalResults),
              total: totalResults
            })}
          </span>
          {selectedResults.length > 0 && (
            <span className="text-sm font-medium text-blue-600">
              {t('selected', { count: selectedResults.length })}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Sort Dropdown */}
          <div className="flex items-center gap-2">
            <SortAsc className="h-4 w-4 text-gray-500" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'relevance' | 'date_desc' | 'date_asc' | 'title')}
              className="text-sm border rounded-lg px-2 py-1 dark:bg-gray-800"
            >
              {sortOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Results per page */}
          <select
            value={resultsPerPage}
            onChange={(e) => setResultsPerPage(Number(e.target.value))}
            className="text-sm border rounded-lg px-2 py-1 dark:bg-gray-800"
          >
            <option value="10">10 {t('perPage')}</option>
            <option value="20">20 {t('perPage')}</option>
            <option value="50">50 {t('perPage')}</option>
            <option value="100">100 {t('perPage')}</option>
          </select>

          {/* Export Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowExportDialog(true)}
            disabled={selectedResults.length === 0 && results.length === 0}
          >
            <Download className="h-4 w-4 mr-1" />
            {t('export')}
          </Button>
        </div>
      </div>

      {/* Select All Checkbox */}
      {results.length > 0 && (
        <div className="mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={selectedResults.length === results.length}
              onChange={handleSelectAll}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm">{t('selectAll')}</span>
          </label>
        </div>
      )}

      {/* Results Grid or List */}
      <div className={
        viewMode === 'grid'
          ? 'grid grid-cols-1 md:grid-cols-2 gap-4'
          : 'space-y-4'
      }>
        {results.map(result => (
          <ResultCard
            key={result.id}
            result={result}
            viewMode={viewMode}
            selected={selectedResults.includes(result.id)}
            onSelect={() => handleSelectResult(result.id)}
          />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-8">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
      )}

      {/* Export Dialog */}
      {showExportDialog && (
        <ExportDialog
          selectedResults={selectedResults.length > 0 ? selectedResults : results.map(r => r.id)}
          onClose={() => setShowExportDialog(false)}
        />
      )}
    </div>
  );
}