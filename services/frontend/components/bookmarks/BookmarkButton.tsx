'use client';

import { useState, useEffect } from 'react';
import { Heart } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/components/providers/ToastProvider';
import { toggleBookmark, isBookmarked } from '@/lib/utils/bookmarks';
import { BookmarkItem } from '@/lib/api/bookmarks';

interface BookmarkButtonProps {
  item: Omit<BookmarkItem, 'id' | 'createdAt' | 'updatedAt'>;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'ghost' | 'outline';
  showLabel?: boolean;
}

export function BookmarkButton({
  item,
  size = 'md',
  variant = 'ghost',
  showLabel = false
}: BookmarkButtonProps) {
  const [bookmarked, setBookmarked] = useState(false);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    checkBookmarkStatus();
  }, [item.itemId]);

  const checkBookmarkStatus = async () => {
    try {
      const status = await isBookmarked(item.itemId);
      setBookmarked(status);
    } catch (error) {
      console.error('Failed to check bookmark status:', error);
    }
  };

  const handleToggle = async () => {
    setLoading(true);

    try {
      console.log('[BookmarkButton] Toggling bookmark for:', item.itemId);
      const result = await toggleBookmark(item);
      console.log('[BookmarkButton] Toggle result:', result);

      setBookmarked(result.added);

      showToast({
        title: result.added ? 'Bookmarked' : 'Removed from bookmarks',
        description: result.synced
          ? result.added
            ? 'Bookmark saved successfully'
            : 'Bookmark removed successfully'
          : 'Saved locally (will sync when online)',
        type: 'success'
      });
    } catch (error: any) {
      console.error('[BookmarkButton] Failed to toggle bookmark:', {
        error,
        message: error?.message,
        response: error?.response?.data,
        status: error?.response?.status
      });

      // Don't show error toast for auth errors - the interceptor will handle redirect
      if (error?.response?.status !== 401 && error?.response?.status !== 403) {
        showToast({
          title: 'Error',
          description: error?.response?.data?.message || 'Failed to update bookmark',
          type: 'error'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleToggle}
      disabled={loading}
      className="flex items-center gap-2"
    >
      <Heart
        className={`h-4 w-4 transition-colors ${
          bookmarked ? 'fill-red-500 text-red-500' : 'text-gray-400'
        }`}
      />
      {showLabel && <span>{bookmarked ? 'Bookmarked' : 'Bookmark'}</span>}
    </Button>
  );
}
