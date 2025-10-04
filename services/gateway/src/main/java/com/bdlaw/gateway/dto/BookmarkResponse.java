package com.bdlaw.gateway.dto;

import lombok.Data;
import java.time.LocalDateTime;
import java.util.Map;

@Data
public class BookmarkResponse {
    private Long id;
    private String itemId;
    private String bookmarkType;
    private String title;
    private String excerpt;
    private String category;
    private String section;
    private String year;
    private String url;
    private Map<String, Object> metadata;
    private String[] tags;
    private String notes;
    private String folderName;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private LocalDateTime lastAccessedAt;
}
