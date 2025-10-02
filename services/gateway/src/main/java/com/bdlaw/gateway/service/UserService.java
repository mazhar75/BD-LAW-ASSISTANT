package com.bdlaw.gateway.service;

import com.bdlaw.gateway.dto.RegisterRequest;
import com.bdlaw.gateway.entity.*;
import com.bdlaw.gateway.repository.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.context.annotation.Lazy;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

@Service
@Slf4j
@Transactional
public class UserService implements UserDetailsService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;
    private final EmailService emailService;
    private final PasswordResetTokenRepository passwordResetTokenRepository;
    private final EmailVerificationTokenRepository emailVerificationTokenRepository;
    private final UserPreferencesRepository userPreferencesRepository;
    private final UsageTrackingRepository usageTrackingRepository;

    public UserService(UserRepository userRepository,
                      RoleRepository roleRepository,
                      @Lazy PasswordEncoder passwordEncoder,
                      EmailService emailService,
                      PasswordResetTokenRepository passwordResetTokenRepository,
                      EmailVerificationTokenRepository emailVerificationTokenRepository,
                      UserPreferencesRepository userPreferencesRepository,
                      UsageTrackingRepository usageTrackingRepository) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
        this.emailService = emailService;
        this.passwordResetTokenRepository = passwordResetTokenRepository;
        this.emailVerificationTokenRepository = emailVerificationTokenRepository;
        this.userPreferencesRepository = userPreferencesRepository;
        this.usageTrackingRepository = usageTrackingRepository;
    }

    @Override
    @Transactional(readOnly = true)  // Read-only transaction to avoid saving
    public User loadUserByUsername(String usernameOrEmail) throws UsernameNotFoundException {
        // First find the user
        User user = userRepository.findByUsernameOrEmail(usernameOrEmail, usernameOrEmail)
            .orElseThrow(() -> new UsernameNotFoundException("User not found with username or email: " + usernameOrEmail));

        // Check if account is locked
        if (!user.isAccountNonLocked()) {
            throw new UsernameNotFoundException("Account is locked until: " + user.getLockedUntil());
        }

        // Manually load roles if they're not loaded
        if (user.getRoles() == null || user.getRoles().isEmpty()) {
            log.info("Manually loading roles for user: {}", user.getUsername());
            Set<Role> roles = loadUserRoles(user.getId());
            // Set roles directly without modifying the collection
            user.setRoles(roles);
        }

        // Log authorities for debugging
        log.info("User {} has {} roles, authorities: {}", user.getUsername(), user.getRoles().size(), user.getAuthorities());

        return user;
    }

    // Helper method to load roles for a user
    private Set<Role> loadUserRoles(Long userId) {
        // Direct query to load roles for the user
        List<Role> roleList = roleRepository.findRolesByUserId(userId);
        return new HashSet<>(roleList);
    }

    public User loadUserById(Long id) {
        return userRepository.findById(id)
            .orElseThrow(() -> new UsernameNotFoundException("User not found with id: " + id));
    }

    public User createUser(RegisterRequest request) {
        // Create new user
        User user = User.builder()
            .username(request.getUsername())
            .email(request.getEmail())
            .password(passwordEncoder.encode(request.getPassword()))
            .fullName(request.getFullName() != null ? request.getFullName() : request.getUsername())
            .phoneNumber(request.getPhoneNumber())
            .isActive(true)
            .isEmailVerified(true)  // TEMPORARY: Set to true for testing
            .build();

        // Assign default role
        Role userRole = roleRepository.findByName(Role.USER)
            .orElseThrow(() -> new RuntimeException("Default role not found"));
        user.addRole(userRole);

        // Save user
        user = userRepository.save(user);

        // Create default preferences
        UserPreferences preferences = UserPreferences.builder()
            .user(user)
            .build();
        userPreferencesRepository.save(preferences);

        // Create email verification token
        EmailVerificationToken verificationToken = EmailVerificationToken.builder()
            .token(UUID.randomUUID().toString())
            .user(user)
            .build();
        emailVerificationTokenRepository.save(verificationToken);

        // Send verification email
        try {
            emailService.sendVerificationEmail(user, verificationToken.getToken());
        } catch (Exception e) {
            log.error("Failed to send verification email to: {}", user.getEmail(), e);
        }

        log.info("New user created: {}", user.getUsername());
        return user;
    }

    @Transactional
    public void updateLastLogin(Long userId) {
        userRepository.updateLastLogin(userId, LocalDateTime.now());
    }

    public boolean existsByUsername(String username) {
        return userRepository.existsByUsername(username);
    }

    public boolean existsByEmail(String email) {
        return userRepository.existsByEmail(email);
    }

    public void changePassword(Long userId, String currentPassword, String newPassword) {
        User user = loadUserById(userId);

        // Verify current password
        if (!passwordEncoder.matches(currentPassword, user.getPassword())) {
            throw new IllegalArgumentException("Current password is incorrect");
        }

        // Validate new password
        if (currentPassword.equals(newPassword)) {
            throw new IllegalArgumentException("New password must be different from current password");
        }

        // Update password
        String encodedPassword = passwordEncoder.encode(newPassword);
        userRepository.updatePassword(userId, encodedPassword);

        log.info("Password changed for user: {}", user.getUsername());
    }

    public void initiatePasswordReset(String email) {
        Optional<User> userOptional = userRepository.findByEmail(email);

        if (userOptional.isPresent()) {
            User user = userOptional.get();

            // Delete any existing reset tokens for this user
            passwordResetTokenRepository.deleteByUser(user);

            // Create new reset token
            PasswordResetToken resetToken = PasswordResetToken.builder()
                .token(UUID.randomUUID().toString())
                .user(user)
                .build();
            passwordResetTokenRepository.save(resetToken);

            // Send reset email
            try {
                emailService.sendPasswordResetEmail(user, resetToken.getToken());
                log.info("Password reset email sent to: {}", email);
            } catch (Exception e) {
                log.error("Failed to send password reset email to: {}", email, e);
            }
        }
        // Don't reveal if email exists for security
    }

    public void resetPassword(String token, String newPassword) {
        PasswordResetToken resetToken = passwordResetTokenRepository.findByToken(token)
            .orElseThrow(() -> new IllegalArgumentException("Invalid or expired reset token"));

        if (!resetToken.isValid()) {
            throw new IllegalArgumentException("Reset token has expired or already been used");
        }

        User user = resetToken.getUser();

        // Update password
        String encodedPassword = passwordEncoder.encode(newPassword);
        userRepository.updatePassword(user.getId(), encodedPassword);

        // Mark token as used
        passwordResetTokenRepository.markAsUsed(token);

        log.info("Password reset successful for user: {}", user.getUsername());
    }

    public void verifyEmail(String token) {
        EmailVerificationToken verificationToken = emailVerificationTokenRepository.findByToken(token)
            .orElseThrow(() -> new IllegalArgumentException("Invalid verification token"));

        if (!verificationToken.isValid()) {
            throw new IllegalArgumentException("Verification token has expired or already been used");
        }

        User user = verificationToken.getUser();
        user.setIsEmailVerified(true);
        userRepository.save(user);

        // Mark token as verified
        emailVerificationTokenRepository.markAsVerified(token);

        log.info("Email verified for user: {}", user.getUsername());
    }

    @Transactional
    public void handleFailedLogin(String usernameOrEmail) {
        userRepository.findByUsernameOrEmail(usernameOrEmail, usernameOrEmail)
            .ifPresent(user -> {
                user.recordFailedLogin();
                userRepository.save(user);
                log.warn("Failed login attempt for user: {}. Attempts: {}",
                    user.getUsername(), user.getFailedLoginAttempts());
            });
    }

    @Transactional
    public void handleSuccessfulLogin(String usernameOrEmail) {
        userRepository.findByUsernameOrEmail(usernameOrEmail, usernameOrEmail)
            .ifPresent(user -> {
                user.recordSuccessfulLogin();
                userRepository.save(user);
            });
    }

    public void assignRole(Long userId, String roleName) {
        User user = loadUserById(userId);
        Role role = roleRepository.findByName(roleName)
            .orElseThrow(() -> new RuntimeException("Role not found: " + roleName));

        user.addRole(role);
        userRepository.save(user);
        log.info("Role {} assigned to user: {}", roleName, user.getUsername());
    }

    public void removeRole(Long userId, String roleName) {
        User user = loadUserById(userId);
        Role role = roleRepository.findByName(roleName)
            .orElseThrow(() -> new RuntimeException("Role not found: " + roleName));

        user.removeRole(role);
        userRepository.save(user);
        log.info("Role {} removed from user: {}", roleName, user.getUsername());
    }

    public void deactivateUser(Long userId) {
        User user = loadUserById(userId);
        user.setIsActive(false);
        userRepository.save(user);
        log.info("User deactivated: {}", user.getUsername());
    }

    public void activateUser(Long userId) {
        User user = loadUserById(userId);
        user.setIsActive(true);
        userRepository.save(user);
        log.info("User activated: {}", user.getUsername());
    }

    public User updateUserProfile(User user) {
        return userRepository.save(user);
    }

    public void verifyPasswordForDeletion(Long userId, String password) {
        User user = loadUserById(userId);
        if (!passwordEncoder.matches(password, user.getPassword())) {
            throw new IllegalArgumentException("Invalid password");
        }
    }

    public void sendVerificationEmail(User user) {
        EmailVerificationToken token = EmailVerificationToken.builder()
            .token(UUID.randomUUID().toString())
            .user(user)
            .build();
        emailVerificationTokenRepository.save(token);

        try {
            emailService.sendVerificationEmail(user, token.getToken());
        } catch (Exception e) {
            log.error("Failed to send verification email to: {}", user.getEmail(), e);
        }
    }

    @Transactional
    public void trackUsage(User user, String endpoint, String method, Integer statusCode,
                          Long responseTimeMs, String query, String userAgent, String ipAddress) {
        UsageTracking tracking = UsageTracking.builder()
            .user(user)
            .endpoint(endpoint)
            .method(method)
            .statusCode(statusCode)
            .responseTimeMs(responseTimeMs)
            .query(query)
            .userAgent(userAgent)
            .ipAddress(ipAddress)
            .build();
        usageTrackingRepository.save(tracking);
    }

    @Transactional
    public UserPreferences getUserPreferences(User user) {
        return userPreferencesRepository.findByUser(user)
            .orElseGet(() -> {
                UserPreferences prefs = UserPreferences.builder()
                    .user(user)
                    .build();
                return userPreferencesRepository.save(prefs);
            });
    }
}