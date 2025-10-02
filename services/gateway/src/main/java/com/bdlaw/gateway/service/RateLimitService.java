package com.bdlaw.gateway.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
@Slf4j
public class RateLimitService {

    private final RedisTemplate<String, Object> redisTemplate;

    @Value("${rate-limit.enabled:true}")
    private boolean rateLimitEnabled;

    @Value("${rate-limit.anonymous.limit:10}")
    private int anonymousLimit;

    @Value("${rate-limit.anonymous.duration:60}")
    private int anonymousDuration;

    @Value("${rate-limit.authenticated.limit:100}")
    private int authenticatedLimit;

    @Value("${rate-limit.authenticated.duration:60}")
    private int authenticatedDuration;

    @Value("${rate-limit.premium.limit:1000}")
    private int premiumLimit;

    @Value("${rate-limit.premium.duration:60}")
    private int premiumDuration;

    /**
     * Check if the request is allowed based on rate limiting
     *
     * @param identifier Client identifier (IP, user ID, API key, etc.)
     * @param userType Type of user (anonymous, authenticated, premium)
     * @return RateLimitResult with allowed status and details
     */
    public RateLimitResult checkRateLimit(String identifier, UserType userType) {
        if (!rateLimitEnabled) {
            return RateLimitResult.allowed();
        }

        String key = "rate_limit:" + userType.name().toLowerCase() + ":" + identifier;

        int limit = getLimit(userType);
        int duration = getDuration(userType);

        // Get current count
        Long currentCount = (Long) redisTemplate.opsForValue().get(key);

        if (currentCount == null) {
            // First request within the window
            redisTemplate.opsForValue().set(key, 1L, duration, TimeUnit.SECONDS);
            return RateLimitResult.builder()
                .allowed(true)
                .limit(limit)
                .remaining(limit - 1)
                .resetAt(Instant.now().plusSeconds(duration).toEpochMilli())
                .build();
        }

        if (currentCount >= limit) {
            // Rate limit exceeded
            Long ttl = redisTemplate.getExpire(key, TimeUnit.SECONDS);
            return RateLimitResult.builder()
                .allowed(false)
                .limit(limit)
                .remaining(0)
                .resetAt(Instant.now().plusSeconds(ttl != null ? ttl : duration).toEpochMilli())
                .build();
        }

        // Increment counter
        Long newCount = redisTemplate.opsForValue().increment(key);
        Long ttl = redisTemplate.getExpire(key, TimeUnit.SECONDS);

        return RateLimitResult.builder()
            .allowed(true)
            .limit(limit)
            .remaining(Math.max(0, limit - newCount.intValue()))
            .resetAt(Instant.now().plusSeconds(ttl != null ? ttl : duration).toEpochMilli())
            .build();
    }

    /**
     * Check rate limit for API key
     *
     * @param apiKey The API key
     * @param customLimit Custom rate limit for this API key (if any)
     * @return RateLimitResult
     */
    public RateLimitResult checkApiKeyRateLimit(String apiKey, Integer customLimit) {
        if (!rateLimitEnabled) {
            return RateLimitResult.allowed();
        }

        String key = "rate_limit:api_key:" + apiKey;
        int limit = customLimit != null ? customLimit : authenticatedLimit;
        int duration = authenticatedDuration;

        Long currentCount = (Long) redisTemplate.opsForValue().get(key);

        if (currentCount == null) {
            redisTemplate.opsForValue().set(key, 1L, duration, TimeUnit.SECONDS);
            return RateLimitResult.builder()
                .allowed(true)
                .limit(limit)
                .remaining(limit - 1)
                .resetAt(Instant.now().plusSeconds(duration).toEpochMilli())
                .build();
        }

        if (currentCount >= limit) {
            Long ttl = redisTemplate.getExpire(key, TimeUnit.SECONDS);
            return RateLimitResult.builder()
                .allowed(false)
                .limit(limit)
                .remaining(0)
                .resetAt(Instant.now().plusSeconds(ttl != null ? ttl : duration).toEpochMilli())
                .build();
        }

        Long newCount = redisTemplate.opsForValue().increment(key);
        Long ttl = redisTemplate.getExpire(key, TimeUnit.SECONDS);

        return RateLimitResult.builder()
            .allowed(true)
            .limit(limit)
            .remaining(Math.max(0, limit - newCount.intValue()))
            .resetAt(Instant.now().plusSeconds(ttl != null ? ttl : duration).toEpochMilli())
            .build();
    }

    /**
     * Reset rate limit for a specific identifier
     *
     * @param identifier Client identifier
     * @param userType User type
     */
    public void resetRateLimit(String identifier, UserType userType) {
        String key = "rate_limit:" + userType.name().toLowerCase() + ":" + identifier;
        redisTemplate.delete(key);
        log.info("Rate limit reset for {}: {}", userType, identifier);
    }

    /**
     * Get current usage for an identifier
     *
     * @param identifier Client identifier
     * @param userType User type
     * @return Current request count
     */
    public long getCurrentUsage(String identifier, UserType userType) {
        String key = "rate_limit:" + userType.name().toLowerCase() + ":" + identifier;
        Long count = (Long) redisTemplate.opsForValue().get(key);
        return count != null ? count : 0;
    }

    private int getLimit(UserType userType) {
        switch (userType) {
            case ANONYMOUS:
                return anonymousLimit;
            case AUTHENTICATED:
                return authenticatedLimit;
            case PREMIUM:
                return premiumLimit;
            default:
                return anonymousLimit;
        }
    }

    private int getDuration(UserType userType) {
        switch (userType) {
            case ANONYMOUS:
                return anonymousDuration;
            case AUTHENTICATED:
                return authenticatedDuration;
            case PREMIUM:
                return premiumDuration;
            default:
                return anonymousDuration;
        }
    }

    public enum UserType {
        ANONYMOUS,
        AUTHENTICATED,
        PREMIUM,
        ADMIN
    }

    @lombok.Data
    @lombok.Builder
    public static class RateLimitResult {
        private boolean allowed;
        private int limit;
        private int remaining;
        private long resetAt;

        public static RateLimitResult allowed() {
            return RateLimitResult.builder()
                .allowed(true)
                .limit(Integer.MAX_VALUE)
                .remaining(Integer.MAX_VALUE)
                .resetAt(0)
                .build();
        }
    }
}