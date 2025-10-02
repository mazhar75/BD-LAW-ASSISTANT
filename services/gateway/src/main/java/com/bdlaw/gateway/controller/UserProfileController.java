package com.bdlaw.gateway.controller;

import com.bdlaw.gateway.dto.*;
import com.bdlaw.gateway.entity.User;
import com.bdlaw.gateway.entity.UserPreferences;
import com.bdlaw.gateway.entity.UsageTracking;
import com.bdlaw.gateway.repository.UserPreferencesRepository;
import com.bdlaw.gateway.repository.UsageTrackingRepository;
import com.bdlaw.gateway.security.JwtTokenProvider;
import com.bdlaw.gateway.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
@Slf4j
public class UserProfileController {

    private final UserService userService;
    private final UserPreferencesRepository preferencesRepository;
    private final UsageTrackingRepository usageTrackingRepository;
    private final JwtTokenProvider tokenProvider;

    @GetMapping("/profile")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<Map<String, Object>> getUserProfile(Authentication authentication) {
        String username = authentication.getName();
        User user = userService.loadUserByUsername(username);

        Map<String, Object> profile = new HashMap<>();
        profile.put("id", user.getId());
        profile.put("username", user.getUsername());
        profile.put("email", user.getEmail());
        profile.put("fullName", user.getFullName());
        profile.put("phoneNumber", user.getPhoneNumber());
        profile.put("roles", user.getRoles());
        profile.put("isActive", user.getIsActive());
        profile.put("isEmailVerified", user.getIsEmailVerified());
        profile.put("createdAt", user.getCreatedAt());
        profile.put("lastLogin", user.getLastLogin());

        return ResponseEntity.ok(profile);
    }

    @PutMapping("/profile")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<Map<String, String>> updateProfile(
            Authentication authentication,
            @RequestBody @Valid UpdateProfileRequest request) {
        String username = authentication.getName();
        User user = userService.loadUserByUsername(username);

        // Update user profile fields
        if (request.getFullName() != null) {
            user.setFullName(request.getFullName());
        }
        if (request.getPhoneNumber() != null) {
            user.setPhoneNumber(request.getPhoneNumber());
        }

        // Save via repository to ensure persistence
        User updatedUser = userService.updateUserProfile(user);

        return ResponseEntity.ok(Map.of(
            "message", "Profile updated successfully",
            "username", updatedUser.getUsername()
        ));
    }

    @PostMapping("/change-password")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<Map<String, String>> changePassword(
            Authentication authentication,
            @RequestBody @Valid ChangePasswordRequest request) {
        String username = authentication.getName();
        User user = userService.loadUserByUsername(username);

        userService.changePassword(user.getId(), request.getCurrentPassword(), request.getNewPassword());

        return ResponseEntity.ok(Map.of("message", "Password changed successfully"));
    }

    @PostMapping("/reset-password")
    public ResponseEntity<Map<String, String>> requestPasswordReset(@RequestBody Map<String, String> request) {
        String email = request.get("email");
        if (email != null && !email.isEmpty()) {
            userService.initiatePasswordReset(email);
        }

        // Always return success to avoid email enumeration
        return ResponseEntity.ok(Map.of(
            "message", "If the email exists, a password reset link has been sent"
        ));
    }

    @PostMapping("/reset-password/confirm")
    public ResponseEntity<Map<String, String>> confirmPasswordReset(@RequestBody ResetPasswordRequest request) {
        userService.resetPassword(request.getToken(), request.getNewPassword());
        return ResponseEntity.ok(Map.of("message", "Password has been reset successfully"));
    }

    @PostMapping("/verify-email/{token}")
    public ResponseEntity<Map<String, String>> verifyEmail(@PathVariable String token) {
        userService.verifyEmail(token);
        return ResponseEntity.ok(Map.of("message", "Email verified successfully"));
    }

    @GetMapping("/preferences")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<UserPreferences> getUserPreferences(Authentication authentication) {
        String username = authentication.getName();
        User user = userService.loadUserByUsername(username);

        UserPreferences preferences = preferencesRepository.findByUser(user)
            .orElseGet(() -> {
                // Create default preferences if none exist
                UserPreferences defaultPrefs = UserPreferences.builder()
                    .user(user)
                    .build();
                return preferencesRepository.save(defaultPrefs);
            });

        return ResponseEntity.ok(preferences);
    }

    @PutMapping("/preferences")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<UserPreferences> updatePreferences(
            Authentication authentication,
            @RequestBody UserPreferences updatedPreferences) {
        String username = authentication.getName();
        User user = userService.loadUserByUsername(username);

        UserPreferences preferences = preferencesRepository.findByUser(user)
            .orElseGet(() -> UserPreferences.builder().user(user).build());

        // Update preferences
        if (updatedPreferences.getLanguage() != null) {
            preferences.setLanguage(updatedPreferences.getLanguage());
        }
        if (updatedPreferences.getTheme() != null) {
            preferences.setTheme(updatedPreferences.getTheme());
        }
        if (updatedPreferences.getEmailNotifications() != null) {
            preferences.setEmailNotifications(updatedPreferences.getEmailNotifications());
        }
        if (updatedPreferences.getSearchHistoryEnabled() != null) {
            preferences.setSearchHistoryEnabled(updatedPreferences.getSearchHistoryEnabled());
        }
        if (updatedPreferences.getResultsPerPage() != null) {
            preferences.setResultsPerPage(updatedPreferences.getResultsPerPage());
        }
        if (updatedPreferences.getDefaultSearchType() != null) {
            preferences.setDefaultSearchType(updatedPreferences.getDefaultSearchType());
        }
        if (updatedPreferences.getAutoTranslate() != null) {
            preferences.setAutoTranslate(updatedPreferences.getAutoTranslate());
        }
        if (updatedPreferences.getPreferredAiModel() != null) {
            preferences.setPreferredAiModel(updatedPreferences.getPreferredAiModel());
        }
        if (updatedPreferences.getShowCitations() != null) {
            preferences.setShowCitations(updatedPreferences.getShowCitations());
        }
        if (updatedPreferences.getHighlightSearchTerms() != null) {
            preferences.setHighlightSearchTerms(updatedPreferences.getHighlightSearchTerms());
        }

        UserPreferences savedPreferences = preferencesRepository.save(preferences);
        return ResponseEntity.ok(savedPreferences);
    }

    @GetMapping("/usage")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<Map<String, Object>> getUserUsage(
            Authentication authentication,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startDate,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endDate) {

        String username = authentication.getName();
        User user = userService.loadUserByUsername(username);

        if (startDate == null) {
            startDate = LocalDateTime.now().minusDays(30);
        }
        if (endDate == null) {
            endDate = LocalDateTime.now();
        }

        Page<UsageTracking> usage = usageTrackingRepository.findByUserAndDateBetween(
            user, startDate, endDate, PageRequest.of(page, size)
        );

        Map<String, Object> response = new HashMap<>();
        response.put("usage", usage.getContent());
        response.put("totalElements", usage.getTotalElements());
        response.put("totalPages", usage.getTotalPages());
        response.put("currentPage", usage.getNumber());

        // Add summary statistics
        Long totalRequests = usageTrackingRepository.countByUserSince(user, startDate);
        Double avgResponseTime = usageTrackingRepository.getAverageResponseTimeByUserSince(user, startDate);
        List<Object[]> topEndpoints = usageTrackingRepository.findTopEndpointsByUser(user);

        response.put("summary", Map.of(
            "totalRequests", totalRequests,
            "averageResponseTime", avgResponseTime != null ? avgResponseTime : 0,
            "topEndpoints", topEndpoints
        ));

        return ResponseEntity.ok(response);
    }

    @GetMapping("/usage/daily")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<List<Object[]>> getDailyUsage(
            Authentication authentication,
            @RequestParam(defaultValue = "30") int days) {

        String username = authentication.getName();
        User user = userService.loadUserByUsername(username);
        LocalDateTime startDate = LocalDateTime.now().minusDays(days);

        List<Object[]> dailyUsage = usageTrackingRepository.getDailyUsageByUserSince(user, startDate);
        return ResponseEntity.ok(dailyUsage);
    }

    @DeleteMapping("/account")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<Map<String, String>> deleteAccount(
            Authentication authentication,
            @RequestBody Map<String, String> request) {

        String password = request.get("password");
        if (password == null || password.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "Password is required"));
        }

        String username = authentication.getName();
        User user = userService.loadUserByUsername(username);

        // Verify password before deletion
        userService.verifyPasswordForDeletion(user.getId(), password);

        // Deactivate instead of hard delete
        userService.deactivateUser(user.getId());

        return ResponseEntity.ok(Map.of("message", "Account has been deactivated successfully"));
    }
}