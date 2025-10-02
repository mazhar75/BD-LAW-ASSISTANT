package com.bdlaw.gateway;

import com.bdlaw.gateway.dto.LoginRequest;
import com.bdlaw.gateway.dto.RegisterRequest;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
public class AuthControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    private RegisterRequest validRegisterRequest;
    private LoginRequest validLoginRequest;

    @BeforeEach
    void setUp() {
        validRegisterRequest = new RegisterRequest();
        validRegisterRequest.setUsername("testuser");
        validRegisterRequest.setEmail("test@example.com");
        validRegisterRequest.setPassword("SecurePass123!");
        validRegisterRequest.setFullName("Test User");

        validLoginRequest = new LoginRequest();
        validLoginRequest.setUsernameOrEmail("testuser");
        validLoginRequest.setPassword("SecurePass123!");
    }

    @Test
    void testRegisterNewUser() throws Exception {
        mockMvc.perform(post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRegisterRequest)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.message").exists())
            .andExpect(jsonPath("$.userId").exists())
            .andExpect(jsonPath("$.username").value("testuser"));
    }

    @Test
    void testRegisterDuplicateUsername() throws Exception {
        // Register first user
        mockMvc.perform(post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRegisterRequest)))
            .andExpect(status().isCreated());

        // Try to register with same username
        validRegisterRequest.setEmail("different@example.com");
        mockMvc.perform(post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRegisterRequest)))
            .andExpect(status().isConflict())
            .andExpect(jsonPath("$.error").value("Username already exists"));
    }

    @Test
    void testLoginWithValidCredentials() throws Exception {
        // First register a user
        mockMvc.perform(post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRegisterRequest)))
            .andExpect(status().isCreated());

        // Then try to login
        mockMvc.perform(post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validLoginRequest)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.accessToken").exists())
            .andExpect(jsonPath("$.refreshToken").exists())
            .andExpect(jsonPath("$.tokenType").value("Bearer"));
    }

    @Test
    void testLoginWithInvalidCredentials() throws Exception {
        validLoginRequest.setPassword("WrongPassword");

        mockMvc.perform(post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validLoginRequest)))
            .andExpect(status().isUnauthorized())
            .andExpect(jsonPath("$.error").exists());
    }

    @Test
    void testForgotPassword() throws Exception {
        mockMvc.perform(post("/api/auth/forgot-password")
                .param("email", "test@example.com"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").exists());
    }

    @Test
    void testVerifyEmail() throws Exception {
        mockMvc.perform(get("/api/auth/verify-email")
                .param("token", "test-token"))
            .andExpect(status().isBadRequest()); // Will fail with invalid token
    }
}