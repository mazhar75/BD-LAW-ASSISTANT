package com.bdlaw.gateway.service;

import com.bdlaw.gateway.dto.*;
import com.bdlaw.gateway.entity.UserBookmark;
import com.bdlaw.gateway.repository.UserBookmarkRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserBookmarkService {

    private final UserBookmarkRepository bookmarkRepository;

    /**
     * Add a new bookmark for a user
     */
    @Transactional
    public BookmarkResponse addBookmark(Long userId, BookmarkRequest request) {
        log.debug("Adding bookmark for user {} with item_id: {}", userId, request.getItemId());

        // Check if bookmark already exists
        if (bookmarkRepository.existsByUserIdAndItemId(userId, request.getItemId())) {
            throw new IllegalArgumentException(
                String.format("Bookmark already exists for item: %s", request.getItemId())
            );
        }

        // Create and save bookmark
        UserBookmark bookmark = UserBookmark.builder()
            .userId(userId)
            .bookmarkType(request.getBookmarkType())
            .itemId(request.getItemId())
            .title(request.getTitle())
            .excerpt(request.getExcerpt())
            .category(request.getCategory())
            .section(request.getSection())
            .year(request.getYear())
            .url(request.getUrl())
            .metadata(request.getMetadata())
            .tags(request.getTags())
            .notes(request.getNotes())
            .folderName(request.getFolderName())
            .build();

        UserBookmark saved = bookmarkRepository.save(bookmark);
        log.info("Bookmark created with ID {} for user {}", saved.getId(), userId);

        return mapToResponse(saved);
    }

    /**
     * Bulk add bookmarks (for sync operation)
     */
    @Transactional
    public List<BookmarkResponse> addBookmarksBulk(Long userId, List<BookmarkRequest> requests) {
        log.debug("Bulk adding {} bookmarks for user {}", requests.size(), userId);

        List<UserBookmark> bookmarks = new ArrayList<>();

        for (BookmarkRequest request : requests) {
            // Skip if already exists
            if (bookmarkRepository.existsByUserIdAndItemId(userId, request.getItemId())) {
                log.debug("Skipping duplicate bookmark: {}", request.getItemId());
                continue;
            }

            UserBookmark bookmark = UserBookmark.builder()
                .userId(userId)
                .bookmarkType(request.getBookmarkType())
                .itemId(request.getItemId())
                .title(request.getTitle())
                .excerpt(request.getExcerpt())
                .category(request.getCategory())
                .section(request.getSection())
                .year(request.getYear())
                .url(request.getUrl())
                .metadata(request.getMetadata())
                .tags(request.getTags())
                .notes(request.getNotes())
                .folderName(request.getFolderName())
                .build();

            bookmarks.add(bookmark);
        }

        List<UserBookmark> saved = bookmarkRepository.saveAll(bookmarks);
        log.info("Bulk created {} bookmarks for user {}", saved.size(), userId);

        return saved.stream()
            .map(this::mapToResponse)
            .collect(Collectors.toList());
    }

    /**
     * Get all bookmarks for a user (paginated)
     */
    @Transactional(readOnly = true)
    public Page<BookmarkResponse> getUserBookmarks(Long userId, int page, int size) {
        log.debug("Fetching bookmarks for user {} (page={}, size={})", userId, page, size);

        Pageable pageable = PageRequest.of(page, size);
        Page<UserBookmark> bookmarks = bookmarkRepository.findByUserIdOrderByCreatedAtDesc(userId, pageable);

        return bookmarks.map(this::mapToResponse);
    }

    /**
     * Get bookmarks by type
     */
    @Transactional(readOnly = true)
    public Page<BookmarkResponse> getUserBookmarksByType(Long userId, String type, int page, int size) {
        log.debug("Fetching {} bookmarks for user {}", type, userId);

        Pageable pageable = PageRequest.of(page, size);
        Page<UserBookmark> bookmarks = bookmarkRepository
            .findByUserIdAndBookmarkTypeOrderByCreatedAtDesc(userId, type, pageable);

        return bookmarks.map(this::mapToResponse);
    }

    /**
     * Get bookmarks by category
     */
    @Transactional(readOnly = true)
    public Page<BookmarkResponse> getUserBookmarksByCategory(Long userId, String category, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<UserBookmark> bookmarks = bookmarkRepository
            .findByUserIdAndCategoryOrderByCreatedAtDesc(userId, category, pageable);

        return bookmarks.map(this::mapToResponse);
    }

    /**
     * Get bookmarks by folder
     */
    @Transactional(readOnly = true)
    public Page<BookmarkResponse> getUserBookmarksByFolder(Long userId, String folder, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<UserBookmark> bookmarks = bookmarkRepository
            .findByUserIdAndFolderNameOrderByCreatedAtDesc(userId, folder, pageable);

        return bookmarks.map(this::mapToResponse);
    }

    /**
     * Get bookmarks by tag
     */
    @Transactional(readOnly = true)
    public Page<BookmarkResponse> getUserBookmarksByTag(Long userId, String tag, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<UserBookmark> bookmarks = bookmarkRepository
            .findByUserIdAndTag(userId, tag, pageable);

        return bookmarks.map(this::mapToResponse);
    }

    /**
     * Search bookmarks
     */
    @Transactional(readOnly = true)
    public Page<BookmarkResponse> searchUserBookmarks(Long userId, String query, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<UserBookmark> bookmarks = bookmarkRepository
            .searchBookmarks(userId, query, pageable);

        return bookmarks.map(this::mapToResponse);
    }

    /**
     * Get specific bookmark by ID
     */
    @Transactional(readOnly = true)
    public BookmarkResponse getBookmarkById(Long userId, Long bookmarkId) {
        UserBookmark bookmark = bookmarkRepository.findById(bookmarkId)
            .orElseThrow(() -> new IllegalArgumentException("Bookmark not found"));

        // Security check: ensure bookmark belongs to requesting user
        if (!bookmark.getUserId().equals(userId)) {
            throw new SecurityException("Access denied: bookmark belongs to another user");
        }

        // Update last accessed timestamp
        bookmarkRepository.updateLastAccessedAt(bookmarkId, userId, LocalDateTime.now());

        return mapToResponse(bookmark);
    }

    /**
     * Update bookmark (notes, tags, folder, metadata)
     */
    @Transactional
    public BookmarkResponse updateBookmark(Long userId, Long bookmarkId, UpdateBookmarkRequest request) {
        log.debug("Updating bookmark {} for user {}", bookmarkId, userId);

        UserBookmark bookmark = bookmarkRepository.findById(bookmarkId)
            .orElseThrow(() -> new IllegalArgumentException("Bookmark not found"));

        // Security check
        if (!bookmark.getUserId().equals(userId)) {
            throw new SecurityException("Access denied: bookmark belongs to another user");
        }

        // Update fields
        if (request.getNotes() != null) {
            bookmark.setNotes(request.getNotes());
        }
        if (request.getTags() != null) {
            bookmark.setTags(request.getTags());
        }
        if (request.getMetadata() != null) {
            bookmark.setMetadata(request.getMetadata());
        }
        if (request.getFolderName() != null) {
            bookmark.setFolderName(request.getFolderName());
        }

        bookmark.markAsAccessed();

        UserBookmark updated = bookmarkRepository.save(bookmark);
        log.info("Bookmark {} updated for user {}", bookmarkId, userId);

        return mapToResponse(updated);
    }

    /**
     * Delete bookmark by ID
     */
    @Transactional
    public void deleteBookmark(Long userId, Long bookmarkId) {
        log.debug("Deleting bookmark {} for user {}", bookmarkId, userId);

        UserBookmark bookmark = bookmarkRepository.findById(bookmarkId)
            .orElseThrow(() -> new IllegalArgumentException("Bookmark not found"));

        // Security check
        if (!bookmark.getUserId().equals(userId)) {
            throw new SecurityException("Access denied: bookmark belongs to another user");
        }

        bookmarkRepository.delete(bookmark);
        log.info("Bookmark {} deleted for user {}", bookmarkId, userId);
    }

    /**
     * Delete bookmark by item ID
     */
    @Transactional
    public void deleteBookmarkByItemId(Long userId, String itemId) {
        log.debug("Deleting bookmark with item_id {} for user {}", itemId, userId);

        bookmarkRepository.deleteByUserIdAndItemId(userId, itemId);
        log.info("Bookmark with item_id {} deleted for user {}", itemId, userId);
    }

    /**
     * Bulk delete bookmarks
     */
    @Transactional
    public void deleteBookmarksBulk(Long userId, List<Long> bookmarkIds) {
        log.debug("Bulk deleting {} bookmarks for user {}", bookmarkIds.size(), userId);

        bookmarkRepository.deleteByUserIdAndIdIn(userId, bookmarkIds);
        log.info("Bulk deleted {} bookmarks for user {}", bookmarkIds.size(), userId);
    }

    /**
     * Check if item is bookmarked
     */
    @Transactional(readOnly = true)
    public boolean isBookmarked(Long userId, String itemId) {
        return bookmarkRepository.existsByUserIdAndItemId(userId, itemId);
    }

    /**
     * Get bookmark count for user
     */
    @Transactional(readOnly = true)
    public long getBookmarkCount(Long userId) {
        return bookmarkRepository.countByUserId(userId);
    }

    /**
     * Get all folders for user
     */
    @Transactional(readOnly = true)
    public List<String> getUserFolders(Long userId) {
        return bookmarkRepository.findDistinctFoldersByUserId(userId);
    }

    /**
     * Get all tags for user
     */
    @Transactional(readOnly = true)
    public List<String> getUserTags(Long userId) {
        return bookmarkRepository.findDistinctTagsByUserId(userId);
    }

    /**
     * Sync local bookmarks with server
     */
    @Transactional
    public SyncResponse syncBookmarks(Long userId, List<BookmarkRequest> localBookmarks) {
        log.info("Syncing {} local bookmarks for user {}", localBookmarks.size(), userId);

        int total = localBookmarks.size();
        int synced = 0;
        int duplicates = 0;
        int failed = 0;

        for (BookmarkRequest request : localBookmarks) {
            try {
                if (bookmarkRepository.existsByUserIdAndItemId(userId, request.getItemId())) {
                    duplicates++;
                    continue;
                }

                UserBookmark bookmark = UserBookmark.builder()
                    .userId(userId)
                    .bookmarkType(request.getBookmarkType())
                    .itemId(request.getItemId())
                    .title(request.getTitle())
                    .excerpt(request.getExcerpt())
                    .category(request.getCategory())
                    .section(request.getSection())
                    .year(request.getYear())
                    .url(request.getUrl())
                    .metadata(request.getMetadata())
                    .tags(request.getTags())
                    .notes(request.getNotes())
                    .folderName(request.getFolderName())
                    .build();

                bookmarkRepository.save(bookmark);
                synced++;
            } catch (Exception e) {
                log.error("Failed to sync bookmark: {}", request.getItemId(), e);
                failed++;
            }
        }

        // Fetch current server state
        List<UserBookmark> serverBookmarks = bookmarkRepository
            .findByUserIdOrderByCreatedAtDesc(userId, Pageable.unpaged())
            .getContent();

        List<BookmarkResponse> serverResponses = serverBookmarks.stream()
            .map(this::mapToResponse)
            .collect(Collectors.toList());

        log.info("Sync complete: total={}, synced={}, duplicates={}, failed={}",
                 total, synced, duplicates, failed);

        return new SyncResponse(total, synced, failed, duplicates, serverResponses);
    }

    /**
     * Map entity to response DTO
     */
    private BookmarkResponse mapToResponse(UserBookmark bookmark) {
        BookmarkResponse response = new BookmarkResponse();
        response.setId(bookmark.getId());
        response.setItemId(bookmark.getItemId());
        response.setBookmarkType(bookmark.getBookmarkType());
        response.setTitle(bookmark.getTitle());
        response.setExcerpt(bookmark.getExcerpt());
        response.setCategory(bookmark.getCategory());
        response.setSection(bookmark.getSection());
        response.setYear(bookmark.getYear());
        response.setUrl(bookmark.getUrl());
        response.setMetadata(bookmark.getMetadata());
        response.setTags(bookmark.getTags());
        response.setNotes(bookmark.getNotes());
        response.setFolderName(bookmark.getFolderName());
        response.setCreatedAt(bookmark.getCreatedAt());
        response.setUpdatedAt(bookmark.getUpdatedAt());
        response.setLastAccessedAt(bookmark.getLastAccessedAt());
        return response;
    }
}
