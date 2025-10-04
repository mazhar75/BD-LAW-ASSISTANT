import { bookmarkApi, BookmarkItem, SyncResponse } from '@/lib/api/bookmarks';

const STORAGE_KEY = 'bd_law_bookmarks';
const SYNC_STATUS_KEY = 'bd_law_bookmarks_sync_status';
const LAST_SYNC_KEY = 'bd_law_bookmarks_last_sync';

/**
 * Get bookmarks from localStorage (offline cache)
 */
export const getLocalBookmarks = (): BookmarkItem[] => {
  if (typeof window === 'undefined') return [];

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Failed to load local bookmarks:', error);
    return [];
  }
};

/**
 * Save bookmarks to localStorage (offline cache)
 */
const saveLocalBookmarks = (bookmarks: BookmarkItem[]): void => {
  if (typeof window === 'undefined') return;

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
    localStorage.setItem(LAST_SYNC_KEY, new Date().toISOString());
  } catch (error) {
    console.error('Failed to save local bookmarks:', error);
  }
};

/**
 * Get all bookmarks (prefer API, fallback to localStorage)
 */
export const getBookmarks = async (): Promise<BookmarkItem[]> => {
  try {
    const response = await bookmarkApi.getAll(0, 1000); // Get first 1000
    const apiBookmarks = response.content;

    // Update local cache
    saveLocalBookmarks(apiBookmarks);

    return apiBookmarks;
  } catch (error) {
    console.warn('API failed, using localStorage cache:', error);
    return getLocalBookmarks();
  }
};

/**
 * Add bookmark (online: API + cache, offline: cache only)
 */
export const addBookmark = async (
  item: Omit<BookmarkItem, 'id' | 'createdAt' | 'updatedAt'>
): Promise<{ success: boolean; synced: boolean; bookmark: BookmarkItem }> => {
  try {
    console.log('[Bookmark] Adding bookmark:', item);
    const saved = await bookmarkApi.add(item);
    console.log('[Bookmark] Successfully added:', saved);

    // Update local cache
    const local = getLocalBookmarks();
    local.unshift(saved);
    saveLocalBookmarks(local);

    return { success: true, synced: true, bookmark: saved };
  } catch (error: any) {
    console.error('[Bookmark] API failed:', {
      error,
      message: error?.message,
      response: error?.response?.data,
      status: error?.response?.status
    });

    // Don't fallback to localStorage on auth errors - let the error propagate
    if (error?.response?.status === 401 || error?.response?.status === 403) {
      throw error;
    }

    // Fallback to localStorage for other errors (offline mode, server error, etc.)
    const localItem: BookmarkItem = {
      ...item,
      id: Date.now(), // Temporary ID
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    const local = getLocalBookmarks();
    local.unshift(localItem);
    saveLocalBookmarks(local);

    return { success: true, synced: false, bookmark: localItem };
  }
};

/**
 * Remove bookmark
 */
export const removeBookmark = async (
  itemId: string
): Promise<{ success: boolean; synced: boolean }> => {
  try {
    await bookmarkApi.deleteByItemId(itemId);

    // Update local cache
    const local = getLocalBookmarks();
    const filtered = local.filter(b => b.itemId !== itemId);
    saveLocalBookmarks(filtered);

    return { success: true, synced: true };
  } catch (error) {
    console.warn('API failed, removing from localStorage only:', error);

    const local = getLocalBookmarks();
    const filtered = local.filter(b => b.itemId !== itemId);
    saveLocalBookmarks(filtered);

    return { success: true, synced: false };
  }
};

/**
 * Check if item is bookmarked
 */
export const isBookmarked = async (itemId: string): Promise<boolean> => {
  try {
    return await bookmarkApi.isBookmarked(itemId);
  } catch (error) {
    const local = getLocalBookmarks();
    return local.some(b => b.itemId === itemId);
  }
};

/**
 * Toggle bookmark
 */
export const toggleBookmark = async (
  item: Omit<BookmarkItem, 'id' | 'createdAt' | 'updatedAt'>
): Promise<{ success: boolean; synced: boolean; added: boolean }> => {
  const bookmarked = await isBookmarked(item.itemId);

  if (bookmarked) {
    const result = await removeBookmark(item.itemId);
    return { ...result, added: false };
  } else {
    const result = await addBookmark(item);
    return { ...result, added: true };
  }
};

/**
 * Sync local bookmarks to server (call on login)
 */
export const syncBookmarks = async (): Promise<SyncResponse> => {
  const localBookmarks = getLocalBookmarks();

  const pendingBookmarks = localBookmarks.filter(b =>
    !b.id || typeof b.id === 'number' && b.id < 1000000
  );

  if (pendingBookmarks.length === 0) {
    try {
      const response = await bookmarkApi.getAll(0, 1000);
      saveLocalBookmarks(response.content);

      return {
        total: 0,
        synced: 0,
        failed: 0,
        duplicates: 0,
        serverBookmarks: response.content
      };
    } catch (error) {
      console.error('Failed to fetch server bookmarks:', error);
      throw error;
    }
  }

  console.log(`Syncing ${pendingBookmarks.length} local bookmarks to server...`);

  try {
    const syncResponse = await bookmarkApi.sync(pendingBookmarks);
    saveLocalBookmarks(syncResponse.serverBookmarks);

    console.log('Sync complete:', syncResponse);
    return syncResponse;
  } catch (error) {
    console.error('Bookmark sync failed:', error);
    throw error;
  }
};

/**
 * Get bookmark count
 */
export const getBookmarksCount = async (): Promise<number> => {
  try {
    return await bookmarkApi.getCount();
  } catch (error) {
    return getLocalBookmarks().length;
  }
};

/**
 * Clear all local bookmarks
 */
export const clearLocalBookmarks = (): void => {
  if (typeof window === 'undefined') return;

  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem(SYNC_STATUS_KEY);
  localStorage.removeItem(LAST_SYNC_KEY);
};
