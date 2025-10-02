package com.bdlaw.gateway.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Map;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@Slf4j
public class ProxyController {

    private final WebClient.Builder webClientBuilder;

    @Value("${services.rag.url:http://localhost:8000}")
    private String ragServiceUrl;

    /**
     * Proxy requests to RAG service
     */
    @PostMapping("/rag/search")
    public Mono<ResponseEntity<Map>> searchProxy(@RequestBody Map<String, Object> request) {
        log.info("Proxying search request to RAG service");

        return webClientBuilder.build()
            .post()
            .uri(ragServiceUrl + "/api/v1/search/")  // Fixed: Added trailing slash
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(request)
            .retrieve()
            .toEntity(Map.class)
            .doOnSuccess(response -> log.info("Search request successful"))
            .doOnError(error -> log.error("Search request failed", error));
    }

    /**
     * Proxy chat/ask requests to RAG service
     */
    @PostMapping("/rag/ask")
    public Mono<ResponseEntity<Map>> askProxy(@RequestBody Map<String, Object> request) {
        log.info("Proxying ask request to RAG service");

        return webClientBuilder.build()
            .post()
            .uri(ragServiceUrl + "/api/v1/query/api/v1/ask")  // Correct RAG endpoint
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(request)
            .retrieve()
            .toEntity(Map.class)
            .doOnSuccess(response -> log.info("Ask request successful"))
            .doOnError(error -> log.error("Ask request failed", error));
    }

    /**
     * Proxy similar laws requests to RAG service
     */
    @GetMapping("/rag/similar/{lawId}")
    public Mono<ResponseEntity<Map>> similarProxy(@PathVariable String lawId) {
        log.info("Proxying similar laws request to RAG service");

        return webClientBuilder.build()
            .get()
            .uri(ragServiceUrl + "/api/v1/query/api/v1/similar?lawId=" + lawId)
            .retrieve()
            .toEntity(Map.class)
            .doOnSuccess(response -> log.info("Similar laws request successful"))
            .doOnError(error -> log.error("Similar laws request failed", error));
    }

    /**
     * Proxy feedback requests to RAG service
     */
    @PostMapping("/rag/feedback")
    public Mono<ResponseEntity<Map>> feedbackProxy(@RequestBody Map<String, Object> request) {
        log.info("Proxying feedback request to RAG service");

        return webClientBuilder.build()
            .post()
            .uri(ragServiceUrl + "/api/v1/query/api/v1/feedback")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(request)
            .retrieve()
            .toEntity(Map.class)
            .doOnSuccess(response -> log.info("Feedback request successful"))
            .doOnError(error -> log.error("Feedback request failed", error));
    }

    /**
     * Proxy health check to RAG service
     */
    @GetMapping("/rag/health")
    public Mono<ResponseEntity<Map>> healthProxy() {
        return webClientBuilder.build()
            .get()
            .uri(ragServiceUrl + "/health/")
            .retrieve()
            .toEntity(Map.class);
    }

    /**
     * Get RAG service stats
     */
    @GetMapping("/rag/stats")
    public Mono<ResponseEntity<Map>> statsProxy() {
        return webClientBuilder.build()
            .get()
            .uri(ragServiceUrl + "/api/v1/admin/stats")
            .retrieve()
            .toEntity(Map.class)
            .onErrorReturn(ResponseEntity.status(HttpStatus.FORBIDDEN).build());
    }

    /**
     * Gateway health check
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
            "status", "UP",
            "service", "API Gateway",
            "timestamp", System.currentTimeMillis()
        ));
    }

    /**
     * Gateway info
     */
    @GetMapping("/info")
    public ResponseEntity<Map<String, Object>> info() {
        return ResponseEntity.ok(Map.of(
            "service", "BD Law API Gateway",
            "version", "1.0.0",
            "description", "API Gateway for BD Law Assistant",
            "endpoints", Map.of(
                "auth", "/api/auth/*",
                "rag", "/api/rag/*",
                "health", "/api/health"
            )
        ));
    }
}