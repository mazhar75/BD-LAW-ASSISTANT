package com.bdlaw.gateway.repository;

import com.bdlaw.gateway.entity.UserBookmark;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface UserBookmarkRepository extends JpaRepository<UserBookmark, Long> {

    // Basic CRUD Operations
    Page<UserBookmark> findByUserIdOrderByCreatedAtDesc(Long userId, Pageable pageable);

    Optional<UserBookmark> findByUserIdAndItemId(Long userId, String itemId);

    boolean existsByUserIdAndItemId(Long userId, String itemId);

    @Modifying
    @Query("DELETE FROM UserBookmark b WHERE b.userId = :userId AND b.itemId = :itemId")
    void deleteByUserIdAndItemId(@Param("userId") Long userId, @Param("itemId") String itemId);

    // Filtered Queries
    Page<UserBookmark> findByUserIdAndBookmarkTypeOrderByCreatedAtDesc(
        Long userId, String bookmarkType, Pageable pageable
    );

    Page<UserBookmark> findByUserIdAndCategoryOrderByCreatedAtDesc(
        Long userId, String category, Pageable pageable
    );

    Page<UserBookmark> findByUserIdAndFolderNameOrderByCreatedAtDesc(
        Long userId, String folderName, Pageable pageable
    );

    @Query(value = "SELECT * FROM auth.user_bookmarks WHERE user_id = :userId AND :tag = ANY(tags) ORDER BY created_at DESC",
           countQuery = "SELECT COUNT(*) FROM auth.user_bookmarks WHERE user_id = :userId AND :tag = ANY(tags)",
           nativeQuery = true)
    Page<UserBookmark> findByUserIdAndTag(@Param("userId") Long userId, @Param("tag") String tag, Pageable pageable);

    // Search Queries
    @Query("SELECT b FROM UserBookmark b WHERE b.userId = :userId AND " +
           "(LOWER(b.title) LIKE LOWER(CONCAT('%', :query, '%')) OR " +
           "LOWER(b.excerpt) LIKE LOWER(CONCAT('%', :query, '%')) OR " +
           "LOWER(b.notes) LIKE LOWER(CONCAT('%', :query, '%'))) " +
           "ORDER BY b.createdAt DESC")
    Page<UserBookmark> searchBookmarks(@Param("userId") Long userId, @Param("query") String query, Pageable pageable);

    // Statistics & Analytics
    long countByUserId(Long userId);

    long countByUserIdAndBookmarkType(Long userId, String bookmarkType);

    Page<UserBookmark> findByUserIdAndLastAccessedAtIsNotNullOrderByLastAccessedAtDesc(
        Long userId, Pageable pageable
    );

    Page<UserBookmark> findByUserIdAndCreatedAtAfterOrderByCreatedAtDesc(
        Long userId, LocalDateTime after, Pageable pageable
    );

    @Query("SELECT DISTINCT b.folderName FROM UserBookmark b WHERE b.userId = :userId AND b.folderName IS NOT NULL ORDER BY b.folderName")
    List<String> findDistinctFoldersByUserId(@Param("userId") Long userId);

    @Query(value = "SELECT DISTINCT UNNEST(tags) as tag FROM auth.user_bookmarks WHERE user_id = :userId ORDER BY tag",
           nativeQuery = true)
    List<String> findDistinctTagsByUserId(@Param("userId") Long userId);

    // Bulk Operations
    @Query("SELECT b FROM UserBookmark b WHERE b.userId = :userId AND b.id IN :ids")
    List<UserBookmark> findByUserIdAndIdIn(@Param("userId") Long userId, @Param("ids") List<Long> ids);

    @Modifying
    @Query("DELETE FROM UserBookmark b WHERE b.userId = :userId AND b.id IN :ids")
    void deleteByUserIdAndIdIn(@Param("userId") Long userId, @Param("ids") List<Long> ids);

    // Update Operations
    @Modifying
    @Query("UPDATE UserBookmark b SET b.lastAccessedAt = :accessedAt WHERE b.id = :id AND b.userId = :userId")
    void updateLastAccessedAt(@Param("id") Long id, @Param("userId") Long userId, @Param("accessedAt") LocalDateTime accessedAt);
}
