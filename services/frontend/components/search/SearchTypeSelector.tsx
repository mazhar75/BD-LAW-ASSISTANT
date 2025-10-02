'use client';

import { useSearchStore } from '@/store/searchStore';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/Button';
import { Info } from 'lucide-react';
import { useState } from 'react';

export function SearchTypeSelector() {
  const t = useTranslations('search.types');
  const { searchType, setSearchType } = useSearchStore();
  const [showTooltip, setShowTooltip] = useState<string | null>(null);

  const searchTypes = [
    {
      id: 'keyword',
      name: t('keyword.name'),
      description: t('keyword.description'),
      icon: '🔤'
    },
    {
      id: 'semantic',
      name: t('semantic.name'),
      description: t('semantic.description'),
      icon: '🧠'
    },
    {
      id: 'hybrid',
      name: t('hybrid.name'),
      description: t('hybrid.description'),
      icon: '⚡'
    }
  ];

  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="font-medium">{t('title')}</span>
        <Info className="h-4 w-4 text-gray-500" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {searchTypes.map((type) => (
          <div key={type.id} className="relative">
            <Button
              variant={searchType === type.id ? 'default' : 'outline'}
              className="w-full justify-start relative"
              onClick={() => setSearchType(type.id as 'keyword' | 'semantic' | 'hybrid')}
              onMouseEnter={() => setShowTooltip(type.id)}
              onMouseLeave={() => setShowTooltip(null)}
            >
              <span className="mr-2 text-lg">{type.icon}</span>
              <span>{type.name}</span>
            </Button>

            {/* Tooltip */}
            {showTooltip === type.id && (
              <div className="absolute z-10 bottom-full mb-2 left-0 right-0 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg">
                <div className="font-semibold mb-1">{type.name}</div>
                <div>{type.description}</div>
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-full">
                  <div className="border-4 border-transparent border-t-gray-900" />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}