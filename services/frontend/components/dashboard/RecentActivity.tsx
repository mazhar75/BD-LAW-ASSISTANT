'use client';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Search, MessageSquare, Clock, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';

interface RecentActivityProps {
  searches: string[];
  chats: Array<{
    id: string;
    title: string;
    date: string;
  }>;
}

export function RecentActivity({ searches, chats }: RecentActivityProps) {
  const t = useTranslations('dashboard');

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Recent Searches */}
      <div>
        <h4 className="font-medium mb-3 flex items-center gap-2">
          <Search className="h-4 w-4" />
          {t('recentSearches')}
        </h4>
        <div className="space-y-2">
          {searches.length > 0 ? (
            searches.slice(0, 5).map((search, index) => (
              <Card key={index} className="p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                <Link href={`/search?q=${encodeURIComponent(search)}`} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Clock className="h-3 w-3 text-gray-400" />
                    <span className="text-sm">{search}</span>
                  </div>
                  <ArrowRight className="h-3 w-3 text-gray-400" />
                </Link>
              </Card>
            ))
          ) : (
            <p className="text-sm text-gray-500">No recent searches</p>
          )}
        </div>
        {searches.length > 5 && (
          <Link href="/search">
            <Button variant="ghost" size="sm" className="mt-2 w-full">
              View all searches
            </Button>
          </Link>
        )}
      </div>

      {/* Recent Chats */}
      <div>
        <h4 className="font-medium mb-3 flex items-center gap-2">
          <MessageSquare className="h-4 w-4" />
          {t('recentChats')}
        </h4>
        <div className="space-y-2">
          {chats.length > 0 ? (
            chats.slice(0, 5).map((chat) => (
              <Card key={chat.id} className="p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                <Link href={`/chat?id=${chat.id}`} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{chat.title}</p>
                    <p className="text-xs text-gray-500">{new Date(chat.date).toLocaleDateString()}</p>
                  </div>
                  <ArrowRight className="h-3 w-3 text-gray-400" />
                </Link>
              </Card>
            ))
          ) : (
            <p className="text-sm text-gray-500">No recent chats</p>
          )}
        </div>
        {chats.length > 5 && (
          <Link href="/chat">
            <Button variant="ghost" size="sm" className="mt-2 w-full">
              View all chats
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
}