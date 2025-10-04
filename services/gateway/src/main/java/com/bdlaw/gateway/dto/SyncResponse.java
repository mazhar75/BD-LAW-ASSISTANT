package com.bdlaw.gateway.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SyncResponse {
    private int total;          // Total bookmarks in sync request
    private int synced;         // Successfully synced
    private int failed;         // Failed to sync
    private int duplicates;     // Already existed
    private List<BookmarkResponse> serverBookmarks;  // Current server state
}
