'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Bookmark, Trash2, ExternalLink, Calendar, Tag, Loader2 } from 'lucide-react';
import { useToast } from '@/components/providers/ToastProvider';
import gatewayClient from '@/lib/api/client';

interface BookmarkItem {
  id: number;
  itemId: string;
  title: string;
  excerpt: string;
  category: string;
  section?: string;
  year?: string;
  url: string;
  createdAt: string;
}

export default function BookmarksPage() {
  const { showToast } = useToast();
  const [bookmarks, setBookmarks] = useState<BookmarkItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  // Load bookmarks from backend on mount
  useEffect(() => {
    loadBookmarks();
  }, []);

  const loadBookmarks = async () => {
    try {
      setIsLoading(true);
      const response = await gatewayClient.get('/api/bookmarks?page=0&size=100');
      console.log('[Bookmarks] Loaded from backend:', response.data);

      if (response.data && response.data.content) {
        setBookmarks(response.data.content);
      }
    } catch (error) {
      console.error('Failed to load bookmarks from backend:', error);
      showToast({
        title: 'Error',
        description: 'Failed to load bookmarks',
        type: 'error',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const removeBookmark = async (id: number) => {
    try {
      await gatewayClient.delete(`/api/bookmarks/${id}`);
      setBookmarks(bookmarks.filter(b => b.id !== id));

      showToast({
        title: 'Bookmark Removed',
        description: 'The bookmark has been removed successfully.',
        type: 'success',
      });
    } catch (error) {
      console.error('Failed to remove bookmark:', error);
      showToast({
        title: 'Error',
        description: 'Failed to remove bookmark',
        type: 'error',
      });
    }
  };

  const clearAllBookmarks = async () => {
    if (window.confirm('Are you sure you want to remove all bookmarks?')) {
      try {
        const bookmarkIds = bookmarks.map(b => b.id);
        await gatewayClient.delete('/api/bookmarks/bulk', { data: bookmarkIds });
        setBookmarks([]);

        showToast({
          title: 'Bookmarks Cleared',
          description: 'All bookmarks have been removed.',
          type: 'success',
        });
      } catch (error) {
        console.error('Failed to clear bookmarks:', error);
        showToast({
          title: 'Error',
          description: 'Failed to clear bookmarks',
          type: 'error',
        });
      }
    }
  };

  const categories = ['all', ...new Set(bookmarks.map(b => b.category).filter(Boolean))];
  const filteredBookmarks = filter === 'all'
    ? bookmarks
    : bookmarks.filter(b => b.category === filter);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Bookmarks</h1>
          <p className="mt-2 text-muted-foreground">
            Your saved legal documents and references
          </p>
        </div>
        {bookmarks.length > 0 && (
          <Button
            variant="outline"
            onClick={clearAllBookmarks}
            className="text-red-600 hover:text-red-700"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear All
          </Button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Bookmark className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Bookmarks</p>
              <p className="text-2xl font-bold">{bookmarks.length}</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <Tag className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Categories</p>
              <p className="text-2xl font-bold">{categories.length - 1}</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Calendar className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Added This Week</p>
              <p className="text-2xl font-bold">
                {bookmarks.filter(b => {
                  const weekAgo = new Date();
                  weekAgo.setDate(weekAgo.getDate() - 7);
                  return new Date(b.createdAt) > weekAgo;
                }).length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Category Filter */}
      {categories.length > 1 && (
        <Card className="p-4">
          <div className="flex gap-2 flex-wrap">
            {categories.map(cat => (
              <Button
                key={cat}
                variant={filter === cat ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter(cat)}
              >
                {cat === 'all' ? 'All' : cat.charAt(0).toUpperCase() + cat.slice(1)}
              </Button>
            ))}
          </div>
        </Card>
      )}

      {/* Bookmarks List */}
      {isLoading ? (
        <Card className="p-12">
          <div className="text-center">
            <Loader2 className="h-12 w-12 text-muted-foreground mx-auto mb-4 animate-spin" />
            <p className="text-muted-foreground">Loading bookmarks...</p>
          </div>
        </Card>
      ) : filteredBookmarks.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <Bookmark className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">
              {filter === 'all' ? 'No Bookmarks Yet' : `No ${filter} Bookmarks`}
            </h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              {filter === 'all'
                ? 'Start bookmarking important legal documents from search results or chat responses.'
                : `You haven't bookmarked any ${filter} documents yet.`
              }
            </p>
            {filter !== 'all' && (
              <Button
                variant="outline"
                onClick={() => setFilter('all')}
                className="mt-4"
              >
                Show All Bookmarks
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredBookmarks.map((bookmark) => (
            <Card key={bookmark.id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-start gap-3">
                    <Bookmark className="h-5 w-5 text-blue-600 mt-1 flex-shrink-0" />
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg mb-2">{bookmark.title}</h3>
                      <p className="text-sm text-muted-foreground mb-3">
                        {bookmark.excerpt}
                      </p>

                      <div className="flex gap-2 flex-wrap mb-2">
                        {bookmark.category && (
                          <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                            {bookmark.category}
                          </span>
                        )}
                        {bookmark.section && (
                          <span className="text-xs px-2 py-1 bg-gray-100 rounded">
                            {bookmark.section}
                          </span>
                        )}
                        {bookmark.year && (
                          <span className="text-xs px-2 py-1 bg-gray-100 rounded">
                            {bookmark.year}
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-muted-foreground">
                        Added on {new Date(bookmark.createdAt).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 ml-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => window.open(bookmark.url, '_blank')}
                    title="Open document"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeBookmark(bookmark.id)}
                    className="text-red-600 hover:text-red-700"
                    title="Remove bookmark"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
