package com.bdlaw.gateway.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.Map;

@Entity
@Table(
    name = "user_bookmarks",
    schema = "auth",
    indexes = {
        @Index(name = "idx_user_bookmarks_user_created", columnList = "user_id,created_at"),
        @Index(name = "idx_user_bookmarks_user_type", columnList = "user_id,bookmark_type"),
        @Index(name = "idx_user_bookmarks_lookup", columnList = "user_id,item_id")
    },
    uniqueConstraints = {
        @UniqueConstraint(name = "unique_user_bookmark", columnNames = {"user_id", "item_id"})
    }
)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserBookmark {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "bookmark_type", nullable = false, length = 50)
    private String bookmarkType;

    @Column(name = "item_id", nullable = false, length = 200)
    private String itemId;

    @Column(nullable = false, length = 500)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String excerpt;

    @Column(length = 100)
    private String category;

    @Column(length = 100)
    private String section;

    @Column(length = 10)
    private String year;

    @Column(length = 500)
    private String url;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private Map<String, Object> metadata;

    @Column(name = "tags", columnDefinition = "text[]")
    @JdbcTypeCode(SqlTypes.ARRAY)
    private String[] tags;

    @Column(columnDefinition = "TEXT")
    private String notes;

    @Column(name = "folder_name", length = 100)
    private String folderName;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @Column(name = "last_accessed_at")
    private LocalDateTime lastAccessedAt;

    @PrePersist
    protected void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    public void markAsAccessed() {
        lastAccessedAt = LocalDateTime.now();
    }
}
