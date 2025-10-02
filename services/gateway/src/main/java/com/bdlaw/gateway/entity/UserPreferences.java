package com.bdlaw.gateway.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "user_preferences", schema = "auth")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserPreferences {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    @Column(name = "language")
    @Builder.Default
    private String language = "en";

    @Column(name = "theme")
    @Builder.Default
    private String theme = "light";

    @Column(name = "email_notifications")
    @Builder.Default
    private Boolean emailNotifications = true;

    @Column(name = "search_history_enabled")
    @Builder.Default
    private Boolean searchHistoryEnabled = true;

    @Column(name = "results_per_page")
    @Builder.Default
    private Integer resultsPerPage = 10;

    @Column(name = "default_search_type")
    @Builder.Default
    private String defaultSearchType = "hybrid";

    @Column(name = "auto_translate")
    @Builder.Default
    private Boolean autoTranslate = false;

    @Column(name = "preferred_ai_model")
    @Builder.Default
    private String preferredAiModel = "gemini";

    @Column(name = "show_citations")
    @Builder.Default
    private Boolean showCitations = true;

    @Column(name = "highlight_search_terms")
    @Builder.Default
    private Boolean highlightSearchTerms = true;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}