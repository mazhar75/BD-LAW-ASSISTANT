package com.bdlaw.gateway.controller;

import com.bdlaw.gateway.dto.*;
import com.bdlaw.gateway.entity.User;
import com.bdlaw.gateway.service.UserBookmarkService;
import com.bdlaw.gateway.service.UserService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("/api/bookmarks")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class BookmarkController {

    private final UserBookmarkService bookmarkService;
    private final UserService userService;

    /**
     * Extract user ID from authentication
     */
    private Long getUserId(Authentication authentication) {
        String username = authentication.getName();
        log.debug("Extracting user ID for username: {}", username);

        // authentication.getName() returns username, so we need to fetch the user
        User user = (User) userService.loadUserByUsername(username);
        if (user == null) {
            log.error("User not found for username: {}", username);
            throw new SecurityException("Invalid user authentication");
        }

        log.debug("Found user ID: {} for username: {}", user.getId(), username);
        return user.getId();
    }

    // ============================================================================
    // Create Endpoints
    // ============================================================================

    @PostMapping
    public ResponseEntity<BookmarkResponse> addBookmark(
            Authentication authentication,
            @Valid @RequestBody BookmarkRequest request) {

        Long userId = getUserId(authentication);
        log.info("User {} adding bookmark for item: {}", userId, request.getItemId());

        BookmarkResponse response = bookmarkService.addBookmark(userId, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @PostMapping("/bulk")
    public ResponseEntity<List<BookmarkResponse>> addBookmarksBulk(
            Authentication authentication,
            @Valid @RequestBody List<BookmarkRequest> requests) {

        Long userId = getUserId(authentication);
        log.info("User {} bulk adding {} bookmarks", userId, requests.size());

        List<BookmarkResponse> responses = bookmarkService.addBookmarksBulk(userId, requests);
        return ResponseEntity.status(HttpStatus.CREATED).body(responses);
    }

    @PostMapping("/sync")
    public ResponseEntity<SyncResponse> syncBookmarks(
            Authentication authentication,
            @Valid @RequestBody List<BookmarkRequest> localBookmarks) {

        Long userId = getUserId(authentication);
        log.info("User {} syncing {} local bookmarks", userId, localBookmarks.size());

        SyncResponse response = bookmarkService.syncBookmarks(userId, localBookmarks);
        return ResponseEntity.ok(response);
    }

    // ============================================================================
    // Read Endpoints
    // ============================================================================

    @GetMapping
    public ResponseEntity<Page<BookmarkResponse>> getBookmarks(
            Authentication authentication,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        Long userId = getUserId(authentication);
        log.debug("User {} fetching bookmarks (page={}, size={})", userId, page, size);

        Page<BookmarkResponse> bookmarks = bookmarkService.getUserBookmarks(userId, page, size);
        return ResponseEntity.ok(bookmarks);
    }

    @GetMapping("/{id}")
    public ResponseEntity<BookmarkResponse> getBookmarkById(
            Authentication authentication,
            @PathVariable Long id) {

        Long userId = getUserId(authentication);
        BookmarkResponse bookmark = bookmarkService.getBookmarkById(userId, id);
        return ResponseEntity.ok(bookmark);
    }

    @GetMapping("/type/{type}")
    public ResponseEntity<Page<BookmarkResponse>> getBookmarksByType(
            Authentication authentication,
            @PathVariable String type,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        Long userId = getUserId(authentication);
        Page<BookmarkResponse> bookmarks = bookmarkService.getUserBookmarksByType(userId, type, page, size);
        return ResponseEntity.ok(bookmarks);
    }

    @GetMapping("/category/{category}")
    public ResponseEntity<Page<BookmarkResponse>> getBookmarksByCategory(
            Authentication authentication,
            @PathVariable String category,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        Long userId = getUserId(authentication);
        Page<BookmarkResponse> bookmarks = bookmarkService.getUserBookmarksByCategory(userId, category, page, size);
        return ResponseEntity.ok(bookmarks);
    }

    @GetMapping("/folder/{folder}")
    public ResponseEntity<Page<BookmarkResponse>> getBookmarksByFolder(
            Authentication authentication,
            @PathVariable String folder,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        Long userId = getUserId(authentication);
        Page<BookmarkResponse> bookmarks = bookmarkService.getUserBookmarksByFolder(userId, folder, page, size);
        return ResponseEntity.ok(bookmarks);
    }

    @GetMapping("/tags/{tag}")
    public ResponseEntity<Page<BookmarkResponse>> getBookmarksByTag(
            Authentication authentication,
            @PathVariable String tag,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        Long userId = getUserId(authentication);
        Page<BookmarkResponse> bookmarks = bookmarkService.getUserBookmarksByTag(userId, tag, page, size);
        return ResponseEntity.ok(bookmarks);
    }

    @GetMapping("/search")
    public ResponseEntity<Page<BookmarkResponse>> searchBookmarks(
            Authentication authentication,
            @RequestParam String query,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        Long userId = getUserId(authentication);
        Page<BookmarkResponse> bookmarks = bookmarkService.searchUserBookmarks(userId, query, page, size);
        return ResponseEntity.ok(bookmarks);
    }

    // ============================================================================
    // Update Endpoints
    // ============================================================================

    @PutMapping("/{id}")
    public ResponseEntity<BookmarkResponse> updateBookmark(
            Authentication authentication,
            @PathVariable Long id,
            @Valid @RequestBody UpdateBookmarkRequest request) {

        Long userId = getUserId(authentication);
        log.info("User {} updating bookmark {}", userId, id);

        BookmarkResponse response = bookmarkService.updateBookmark(userId, id, request);
        return ResponseEntity.ok(response);
    }

    // ============================================================================
    // Delete Endpoints
    // ============================================================================

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteBookmark(
            Authentication authentication,
            @PathVariable Long id) {

        Long userId = getUserId(authentication);
        log.info("User {} deleting bookmark {}", userId, id);

        bookmarkService.deleteBookmark(userId, id);
        return ResponseEntity.noContent().build();
    }

    @DeleteMapping("/item/{itemId}")
    public ResponseEntity<Void> deleteBookmarkByItemId(
            Authentication authentication,
            @PathVariable String itemId) {

        Long userId = getUserId(authentication);
        log.info("User {} deleting bookmark with item_id: {}", userId, itemId);

        bookmarkService.deleteBookmarkByItemId(userId, itemId);
        return ResponseEntity.noContent().build();
    }

    @DeleteMapping("/bulk")
    public ResponseEntity<Void> deleteBookmarksBulk(
            Authentication authentication,
            @RequestBody List<Long> bookmarkIds) {

        Long userId = getUserId(authentication);
        log.info("User {} bulk deleting {} bookmarks", userId, bookmarkIds.size());

        bookmarkService.deleteBookmarksBulk(userId, bookmarkIds);
        return ResponseEntity.noContent().build();
    }

    // ============================================================================
    // Utility Endpoints
    // ============================================================================

    @GetMapping("/check/{itemId}")
    public ResponseEntity<Boolean> isBookmarked(
            Authentication authentication,
            @PathVariable String itemId) {

        Long userId = getUserId(authentication);
        boolean bookmarked = bookmarkService.isBookmarked(userId, itemId);
        return ResponseEntity.ok(bookmarked);
    }

    @GetMapping("/count")
    public ResponseEntity<Long> getBookmarkCount(Authentication authentication) {
        Long userId = getUserId(authentication);
        long count = bookmarkService.getBookmarkCount(userId);
        return ResponseEntity.ok(count);
    }

    @GetMapping("/folders")
    public ResponseEntity<List<String>> getUserFolders(Authentication authentication) {
        Long userId = getUserId(authentication);
        List<String> folders = bookmarkService.getUserFolders(userId);
        return ResponseEntity.ok(folders);
    }

    @GetMapping("/tags")
    public ResponseEntity<List<String>> getUserTags(Authentication authentication) {
        Long userId = getUserId(authentication);
        List<String> tags = bookmarkService.getUserTags(userId);
        return ResponseEntity.ok(tags);
    }
}
