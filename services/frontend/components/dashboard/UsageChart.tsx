'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { useTranslations } from 'next-intl';

interface UsageChartProps {
  data: {
    thisWeek?: { searches: number; chats: number };
    thisMonth?: { searches: number; chats: number };
  } | null;
}

const mockChartData = [
  { day: 'Mon', searches: 12, chats: 5 },
  { day: 'Tue', searches: 19, chats: 8 },
  { day: 'Wed', searches: 15, chats: 3 },
  { day: 'Thu', searches: 22, chats: 12 },
  { day: 'Fri', searches: 28, chats: 7 },
  { day: 'Sat', searches: 8, chats: 2 },
  { day: 'Sun', searches: 14, chats: 6 }
];

export function UsageChart({ data }: UsageChartProps) {
  const t = useTranslations('dashboard');
  const [period, setPeriod] = useState<'week' | 'month'>('week');

  const maxValue = Math.max(...mockChartData.map(d => Math.max(d.searches, d.chats)));

  return (
    <div>
      {/* Period Selector */}
      <div className="flex justify-end gap-2 mb-4">
        <Button
          variant={period === 'week' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setPeriod('week')}
        >
          {t('thisWeek')}
        </Button>
        <Button
          variant={period === 'month' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setPeriod('month')}
        >
          {t('thisMonth')}
        </Button>
      </div>

      {/* Simple Bar Chart */}
      <div className="space-y-4">
        {/* Chart Bars */}
        <div className="flex items-end justify-between gap-2 h-48">
          {mockChartData.map((item, index) => (
            <div key={index} className="flex-1 flex flex-col items-center justify-end gap-2">
              <div className="w-full flex gap-1 items-end">
                <div
                  className="flex-1 bg-blue-500 rounded-t"
                  style={{
                    height: `${(item.searches / maxValue) * 100}%`,
                    minHeight: '4px'
                  }}
                />
                <div
                  className="flex-1 bg-green-500 rounded-t"
                  style={{
                    height: `${(item.chats / maxValue) * 100}%`,
                    minHeight: '4px'
                  }}
                />
              </div>
              <span className="text-xs text-gray-600 dark:text-gray-400">{item.day}</span>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded" />
            <span className="text-sm">Searches</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded" />
            <span className="text-sm">Chats</span>
          </div>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Searches</p>
            <p className="text-xl font-bold">
              {period === 'week' ? data?.thisWeek?.searches || 0 : data?.thisMonth?.searches || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Chats</p>
            <p className="text-xl font-bold">
              {period === 'week' ? data?.thisWeek?.chats || 0 : data?.thisMonth?.chats || 0}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}