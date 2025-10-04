import gatewayClient from './client';

// ============================================================================
// Types
// ============================================================================

export interface BookmarkItem {
  id?: number;
  itemId: string;
  bookmarkType: 'search_result' | 'chat_citation' | 'law_document' | 'law_section';
  title: string;
  excerpt: string;
  category?: string;
  section?: string;
  year?: string;
  url: string;
  metadata?: Record<string, any>;
  tags?: string[];
  notes?: string;
  folderName?: string;
  createdAt?: string;
  updatedAt?: string;
  lastAccessedAt?: string;
}

export interface PageResponse<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  size: number;
  number: number;
}

export interface SyncResponse {
  total: number;
  synced: number;
  failed: number;
  duplicates: number;
  serverBookmarks: BookmarkItem[];
}

// ============================================================================
// Bookmark API Client
// ============================================================================

export const bookmarkApi = {
  /**
   * Add a new bookmark
   */
  async add(bookmark: Omit<BookmarkItem, 'id' | 'createdAt' | 'updatedAt'>): Promise<BookmarkItem> {
    const response = await gatewayClient.post('/api/bookmarks', bookmark);
    return response.data;
  },

  /**
   * Get all bookmarks (paginated)
   */
  async getAll(page = 0, size = 20): Promise<PageResponse<BookmarkItem>> {
    const response = await gatewayClient.get('/api/bookmarks', {
      params: { page, size }
    });
    return response.data;
  },

  /**
   * Get bookmark by ID
   */
  async getById(id: number): Promise<BookmarkItem> {
    const response = await gatewayClient.get(`/api/bookmarks/${id}`);
    return response.data;
  },

  /**
   * Get bookmarks by type
   */
  async getByType(type: string, page = 0, size = 20): Promise<PageResponse<BookmarkItem>> {
    const response = await gatewayClient.get(`/api/bookmarks/type/${type}`, {
      params: { page, size }
    });
    return response.data;
  },

  /**
   * Get bookmarks by category
   */
  async getByCategory(category: string, page = 0, size = 20): Promise<PageResponse<BookmarkItem>> {
    const response = await gatewayClient.get(`/api/bookmarks/category/${category}`, {
      params: { page, size }
    });
    return response.data;
  },

  /**
   * Get bookmarks in folder
   */
  async getByFolder(folder: string, page = 0, size = 20): Promise<PageResponse<BookmarkItem>> {
    const response = await gatewayClient.get(`/api/bookmarks/folder/${folder}`, {
      params: { page, size }
    });
    return response.data;
  },

  /**
   * Get bookmarks by tag
   */
  async getByTag(tag: string, page = 0, size = 20): Promise<PageResponse<BookmarkItem>> {
    const response = await gatewayClient.get(`/api/bookmarks/tags/${tag}`, {
      params: { page, size }
    });
    return response.data;
  },

  /**
   * Search bookmarks
   */
  async search(query: string, page = 0, size = 20): Promise<PageResponse<BookmarkItem>> {
    const response = await gatewayClient.get('/api/bookmarks/search', {
      params: { query, page, size }
    });
    return response.data;
  },

  /**
   * Update bookmark
   */
  async update(
    id: number,
    updates: { notes?: string; tags?: string[]; metadata?: Record<string, any>; folderName?: string }
  ): Promise<BookmarkItem> {
    const response = await gatewayClient.put(`/api/bookmarks/${id}`, updates);
    return response.data;
  },

  /**
   * Delete bookmark by ID
   */
  async delete(id: number): Promise<void> {
    await gatewayClient.delete(`/api/bookmarks/${id}`);
  },

  /**
   * Delete bookmark by item ID
   */
  async deleteByItemId(itemId: string): Promise<void> {
    await gatewayClient.delete(`/api/bookmarks/item/${itemId}`);
  },

  /**
   * Bulk delete bookmarks
   */
  async deleteBulk(ids: number[]): Promise<void> {
    await gatewayClient.delete('/api/bookmarks/bulk', {
      data: ids
    });
  },

  /**
   * Check if item is bookmarked
   */
  async isBookmarked(itemId: string): Promise<boolean> {
    const response = await gatewayClient.get(`/api/bookmarks/check/${itemId}`);
    return response.data;
  },

  /**
   * Get bookmark count
   */
  async getCount(): Promise<number> {
    const response = await gatewayClient.get('/api/bookmarks/count');
    return response.data;
  },

  /**
   * Get all folders
   */
  async getFolders(): Promise<string[]> {
    const response = await gatewayClient.get('/api/bookmarks/folders');
    return response.data;
  },

  /**
   * Get all tags
   */
  async getTags(): Promise<string[]> {
    const response = await gatewayClient.get('/api/bookmarks/tags');
    return response.data;
  },

  /**
   * Sync local bookmarks with server
   */
  async sync(localBookmarks: Omit<BookmarkItem, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<SyncResponse> {
    const response = await gatewayClient.post('/api/bookmarks/sync', localBookmarks);
    return response.data;
  },

  /**
   * Bulk add bookmarks
   */
  async addBulk(bookmarks: Omit<BookmarkItem, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<BookmarkItem[]> {
    const response = await gatewayClient.post('/api/bookmarks/bulk', bookmarks);
    return response.data;
  }
};
