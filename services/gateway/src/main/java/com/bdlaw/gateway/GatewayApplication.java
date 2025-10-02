package com.bdlaw.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

/**
 * Main application class for BD Law API Gateway
 *
 * This gateway service handles:
 * - Authentication and authorization
 * - Request routing to microservices
 * - Rate limiting and throttling
 * - Caching with Redis
 * - API documentation
 */
@SpringBootApplication
@EnableCaching
public class GatewayApplication {

    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }
}