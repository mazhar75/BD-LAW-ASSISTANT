package com.bdlaw.gateway.dto;

import jakarta.validation.constraints.Size;
import lombok.Data;
import java.util.Map;

@Data
public class UpdateBookmarkRequest {

    @Size(max = 2000, message = "Notes must not exceed 2000 characters")
    private String notes;

    private String[] tags;

    private Map<String, Object> metadata;

    @Size(max = 100, message = "Folder name must not exceed 100 characters")
    private String folderName;
}
