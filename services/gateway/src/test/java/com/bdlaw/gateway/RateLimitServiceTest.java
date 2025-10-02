package com.bdlaw.gateway;

import com.bdlaw.gateway.service.RateLimitService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.test.context.ActiveProfiles;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@ActiveProfiles("test")
public class RateLimitServiceTest {

    @Autowired
    private RateLimitService rateLimitService;

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    @BeforeEach
    void setUp() {
        // Clear Redis before each test
        redisTemplate.getConnectionFactory().getConnection().flushAll();
    }

    @Test
    void testAnonymousRateLimit() {
        String identifier = "test-ip";
        RateLimitService.UserType userType = RateLimitService.UserType.ANONYMOUS;

        // First request should be allowed
        RateLimitService.RateLimitResult result = rateLimitService.checkRateLimit(identifier, userType);
        assertTrue(result.isAllowed());
        assertEquals(9, result.getRemaining()); // 10 - 1

        // Use up remaining requests
        for (int i = 0; i < 9; i++) {
            result = rateLimitService.checkRateLimit(identifier, userType);
            assertTrue(result.isAllowed());
        }

        // Next request should be blocked
        result = rateLimitService.checkRateLimit(identifier, userType);
        assertFalse(result.isAllowed());
        assertEquals(0, result.getRemaining());
    }

    @Test
    void testAuthenticatedRateLimit() {
        String identifier = "user:123";
        RateLimitService.UserType userType = RateLimitService.UserType.AUTHENTICATED;

        // Authenticated users should have higher limit
        RateLimitService.RateLimitResult result = rateLimitService.checkRateLimit(identifier, userType);
        assertTrue(result.isAllowed());
        assertEquals(100, result.getLimit());
        assertEquals(99, result.getRemaining());
    }

    @Test
    void testPremiumRateLimit() {
        String identifier = "user:premium";
        RateLimitService.UserType userType = RateLimitService.UserType.PREMIUM;

        // Premium users should have highest limit
        RateLimitService.RateLimitResult result = rateLimitService.checkRateLimit(identifier, userType);
        assertTrue(result.isAllowed());
        assertEquals(1000, result.getLimit());
        assertEquals(999, result.getRemaining());
    }

    @Test
    void testRateLimitReset() {
        String identifier = "test-reset";
        RateLimitService.UserType userType = RateLimitService.UserType.ANONYMOUS;

        // Use up some requests
        for (int i = 0; i < 5; i++) {
            rateLimitService.checkRateLimit(identifier, userType);
        }

        // Check current usage
        long usage = rateLimitService.getCurrentUsage(identifier, userType);
        assertEquals(5, usage);

        // Reset rate limit
        rateLimitService.resetRateLimit(identifier, userType);

        // Check usage after reset
        usage = rateLimitService.getCurrentUsage(identifier, userType);
        assertEquals(0, usage);

        // Should be able to make requests again
        RateLimitService.RateLimitResult result = rateLimitService.checkRateLimit(identifier, userType);
        assertTrue(result.isAllowed());
        assertEquals(9, result.getRemaining());
    }

    @Test
    void testApiKeyRateLimit() {
        String apiKey = "test-api-key";
        Integer customLimit = 500;

        // Test with custom limit
        RateLimitService.RateLimitResult result = rateLimitService.checkApiKeyRateLimit(apiKey, customLimit);
        assertTrue(result.isAllowed());
        assertEquals(500, result.getLimit());
        assertEquals(499, result.getRemaining());

        // Test without custom limit (should use authenticated limit)
        String anotherApiKey = "another-api-key";
        result = rateLimitService.checkApiKeyRateLimit(anotherApiKey, null);
        assertTrue(result.isAllowed());
        assertEquals(100, result.getLimit()); // Default authenticated limit
    }
}