package com.bdlaw.gateway.controller;

import com.bdlaw.gateway.dto.LoginRequest;
import com.bdlaw.gateway.dto.LoginResponse;
import com.bdlaw.gateway.dto.RegisterRequest;
import com.bdlaw.gateway.entity.User;
import com.bdlaw.gateway.security.JwtTokenProvider;
import com.bdlaw.gateway.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Authentication", description = "Authentication and user management endpoints")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final JwtTokenProvider tokenProvider;
    private final UserService userService;

    @Value("${jwt.expiration}")
    private Long jwtExpiration;

    @PostMapping("/login")
    @Operation(summary = "User login", description = "Authenticate user and receive JWT tokens")
    public ResponseEntity<?> authenticateUser(@Valid @RequestBody LoginRequest loginRequest) {
        try {
            Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                    loginRequest.getUsernameOrEmail(),
                    loginRequest.getPassword()
                )
            );

            SecurityContextHolder.getContext().setAuthentication(authentication);

            User user = (User) authentication.getPrincipal();
            // Reload user with roles to ensure they're included in the JWT
            user = userService.loadUserByUsername(user.getUsername());
            String accessToken = tokenProvider.generateToken(user);
            String refreshToken = tokenProvider.generateRefreshToken(user);

            // Update last login
            // TODO: Fix duplicate role constraint violation
            // userService.updateLastLogin(user.getId());

            LoginResponse response = LoginResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .expiresIn(jwtExpiration / 1000) // Convert to seconds
                .user(LoginResponse.UserDto.builder()
                    .id(user.getId())
                    .username(user.getUsername())
                    .email(user.getEmail())
                    .fullName(user.getFullName())
                    .roles(user.getAuthorities().stream()
                        .map(GrantedAuthority::getAuthority)
                        .collect(Collectors.toList()))
                    .isEmailVerified(user.getIsEmailVerified())
                    .isActive(user.getIsActive())
                    .build())
                .build();

            log.info("User {} logged in successfully", user.getUsername());
            return ResponseEntity.ok(response);

        } catch (AuthenticationException e) {
            log.error("Authentication failed for user: {}", loginRequest.getUsernameOrEmail());
            Map<String, String> error = new HashMap<>();
            error.put("error", "Invalid username/email or password");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(error);
        }
    }

    @PostMapping("/register")
    @Operation(summary = "User registration", description = "Register a new user account")
    public ResponseEntity<?> registerUser(@Valid @RequestBody RegisterRequest registerRequest) {
        try {
            // Check if username exists
            if (userService.existsByUsername(registerRequest.getUsername())) {
                Map<String, String> error = new HashMap<>();
                error.put("error", "Username is already taken");
                return ResponseEntity.badRequest().body(error);
            }

            // Check if email exists
            if (userService.existsByEmail(registerRequest.getEmail())) {
                Map<String, String> error = new HashMap<>();
                error.put("error", "Email is already registered");
                return ResponseEntity.badRequest().body(error);
            }

            // Check terms acceptance (optional for development)
            // TODO: Enable this check in production
            /*
            if (!Boolean.TRUE.equals(registerRequest.getAcceptTerms())) {
                Map<String, String> error = new HashMap<>();
                error.put("error", "You must accept the terms and conditions");
                return ResponseEntity.badRequest().body(error);
            }
            */

            // Create new user
            User user = userService.createUser(registerRequest);

            // Reload user with roles to ensure they're included in the JWT
            user = userService.loadUserByUsername(user.getUsername());

            // Generate tokens
            String accessToken = tokenProvider.generateToken(user);
            String refreshToken = tokenProvider.generateRefreshToken(user);

            LoginResponse response = LoginResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .expiresIn(jwtExpiration / 1000)
                .user(LoginResponse.UserDto.builder()
                    .id(user.getId())
                    .username(user.getUsername())
                    .email(user.getEmail())
                    .fullName(user.getFullName())
                    .roles(user.getAuthorities().stream()
                        .map(GrantedAuthority::getAuthority)
                        .collect(Collectors.toList()))
                    .isEmailVerified(true)  // TEMPORARY: Set to true for testing
                    .isActive(true)
                    .build())
                .build();

            log.info("New user registered: {}", user.getUsername());
            return ResponseEntity.status(HttpStatus.CREATED).body(response);

        } catch (Exception e) {
            log.error("Registration failed: ", e);
            Map<String, String> error = new HashMap<>();
            error.put("error", "Registration failed: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    @PostMapping("/refresh")
    @Operation(summary = "Refresh access token", description = "Use refresh token to get new access token")
    public ResponseEntity<?> refreshToken(@RequestHeader("Refresh-Token") String refreshToken) {
        try {
            if (!tokenProvider.validateToken(refreshToken)) {
                Map<String, String> error = new HashMap<>();
                error.put("error", "Invalid refresh token");
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(error);
            }

            String username = tokenProvider.getUsernameFromToken(refreshToken);
            User user = userService.loadUserByUsername(username);

            String newAccessToken = tokenProvider.generateToken(user);

            Map<String, Object> response = new HashMap<>();
            response.put("accessToken", newAccessToken);
            response.put("tokenType", "Bearer");
            response.put("expiresIn", jwtExpiration / 1000);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("Token refresh failed: ", e);
            Map<String, String> error = new HashMap<>();
            error.put("error", "Token refresh failed");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(error);
        }
    }

    @PostMapping("/logout")
    @Operation(summary = "User logout", description = "Logout and invalidate tokens")
    public ResponseEntity<?> logout(@RequestHeader("Authorization") String token) {
        // In a stateless JWT setup, logout is typically handled on the client side
        // However, you can implement token blacklisting if needed
        SecurityContextHolder.clearContext();

        Map<String, String> response = new HashMap<>();
        response.put("message", "Logged out successfully");
        return ResponseEntity.ok(response);
    }

    @GetMapping("/profile")
    @Operation(summary = "Get user profile", description = "Get current user's profile information")
    public ResponseEntity<?> getUserProfile(Authentication authentication) {
        if (authentication == null || !authentication.isAuthenticated()) {
            Map<String, String> error = new HashMap<>();
            error.put("error", "Not authenticated");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(error);
        }

        User user = (User) authentication.getPrincipal();

        LoginResponse.UserDto userDto = LoginResponse.UserDto.builder()
            .id(user.getId())
            .username(user.getUsername())
            .email(user.getEmail())
            .fullName(user.getFullName())
            .roles(user.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toList()))
            .isEmailVerified(user.getIsEmailVerified())
            .isActive(user.getIsActive())
            .build();

        return ResponseEntity.ok(userDto);
    }

    @PostMapping("/change-password")
    @Operation(summary = "Change password", description = "Change user password")
    public ResponseEntity<?> changePassword(
            @RequestBody Map<String, String> request,
            Authentication authentication) {

        if (authentication == null || !authentication.isAuthenticated()) {
            Map<String, String> error = new HashMap<>();
            error.put("error", "Not authenticated");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(error);
        }

        String currentPassword = request.get("currentPassword");
        String newPassword = request.get("newPassword");

        if (currentPassword == null || newPassword == null) {
            Map<String, String> error = new HashMap<>();
            error.put("error", "Current password and new password are required");
            return ResponseEntity.badRequest().body(error);
        }

        try {
            User user = (User) authentication.getPrincipal();
            userService.changePassword(user.getId(), currentPassword, newPassword);

            Map<String, String> response = new HashMap<>();
            response.put("message", "Password changed successfully");
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("Password change failed: ", e);
            Map<String, String> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(error);
        }
    }

    @PostMapping("/forgot-password")
    @Operation(summary = "Forgot password", description = "Request password reset email")
    public ResponseEntity<?> forgotPassword(@RequestBody Map<String, String> request) {
        String email = request.get("email");

        if (email == null || email.isEmpty()) {
            Map<String, String> error = new HashMap<>();
            error.put("error", "Email is required");
            return ResponseEntity.badRequest().body(error);
        }

        try {
            userService.initiatePasswordReset(email);

            Map<String, String> response = new HashMap<>();
            response.put("message", "Password reset instructions sent to your email");
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            // Don't reveal if email exists or not
            Map<String, String> response = new HashMap<>();
            response.put("message", "Password reset instructions sent to your email");
            return ResponseEntity.ok(response);
        }
    }
}