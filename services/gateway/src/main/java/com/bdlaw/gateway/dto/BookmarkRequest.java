package com.bdlaw.gateway.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.util.Map;

@Data
public class BookmarkRequest {

    @NotBlank(message = "Item ID is required")
    @Size(max = 200, message = "Item ID must not exceed 200 characters")
    private String itemId;

    @NotBlank(message = "Bookmark type is required")
    @Pattern(regexp = "search_result|chat_citation|law_document|law_section",
             message = "Invalid bookmark type")
    private String bookmarkType;

    @NotBlank(message = "Title is required")
    @Size(max = 500, message = "Title must not exceed 500 characters")
    private String title;

    @Size(max = 5000, message = "Excerpt must not exceed 5000 characters")
    private String excerpt;

    @Size(max = 100, message = "Category must not exceed 100 characters")
    private String category;

    @Size(max = 100, message = "Section must not exceed 100 characters")
    private String section;

    @Size(max = 10, message = "Year must not exceed 10 characters")
    private String year;

    @Size(max = 500, message = "URL must not exceed 500 characters")
    private String url;

    private Map<String, Object> metadata;

    private String[] tags;

    @Size(max = 2000, message = "Notes must not exceed 2000 characters")
    private String notes;

    @Size(max = 100, message = "Folder name must not exceed 100 characters")
    private String folderName;
}
