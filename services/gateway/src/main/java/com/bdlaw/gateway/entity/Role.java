package com.bdlaw.gateway.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;

@Entity
@Table(name = "roles", schema = "auth")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Role {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false, length = 50)
    private String name;

    @Column(length = 255)
    private String description;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @ManyToMany(mappedBy = "roles", fetch = FetchType.LAZY)
    private Set<User> users = new HashSet<>();

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    // Predefined role constants
    public static final String USER = "ROLE_USER";
    public static final String PREMIUM = "ROLE_PREMIUM";
    public static final String ADMIN = "ROLE_ADMIN";

    // Helper methods
    public boolean isAdmin() {
        return ADMIN.equals(this.name);
    }

    public boolean isPremium() {
        return PREMIUM.equals(this.name);
    }

    public boolean isUser() {
        return USER.equals(this.name);
    }
}