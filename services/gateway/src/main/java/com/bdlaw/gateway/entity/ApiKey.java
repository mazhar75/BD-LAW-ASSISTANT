package com.bdlaw.gateway.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.Map;

@Entity
@Table(name = "api_keys", schema = "auth")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ApiKey {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "key_value", unique = true, nullable = false)
    private String keyValue;

    @Column(length = 100)
    private String name;

    @Column(length = 255)
    private String description;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "expires_at")
    private LocalDateTime expiresAt;

    @Column(name = "last_used_at")
    private LocalDateTime lastUsedAt;

    @Column(name = "is_active")
    @Builder.Default
    private Boolean isActive = true;

    @Column(name = "rate_limit_override")
    private Integer rateLimitOverride;

    @Column(name = "allowed_ips", columnDefinition = "TEXT")
    private String allowedIps;

    @Column(name = "permissions", columnDefinition = "JSONB")
    @Convert(converter = JsonbConverter.class)
    private Map<String, Object> permissions;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (expiresAt == null) {
            expiresAt = LocalDateTime.now().plusYears(1);
        }
    }

    // Helper methods
    public boolean isExpired() {
        return expiresAt != null && LocalDateTime.now().isAfter(expiresAt);
    }

    public boolean isValid() {
        return isActive && !isExpired();
    }

    public void recordUsage() {
        this.lastUsedAt = LocalDateTime.now();
    }

    public boolean isIpAllowed(String ipAddress) {
        if (allowedIps == null || allowedIps.isEmpty()) {
            return true; // No IP restriction
        }
        String[] ips = allowedIps.split(",");
        for (String ip : ips) {
            if (ip.trim().equals(ipAddress)) {
                return true;
            }
        }
        return false;
    }

    public boolean hasPermission(String permission) {
        if (permissions == null) {
            return false;
        }
        return permissions.containsKey(permission) &&
               Boolean.TRUE.equals(permissions.get(permission));
    }
}