package com.bdlaw.gateway.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.HttpClientErrorException;

import java.util.Map;

@RestController
@RequestMapping("/api/rag")
@Slf4j
@CrossOrigin(origins = "*")
public class RagProxyController {

    @Value("${services.rag.url:http://localhost:8000}")
    private String ragServiceUrl;

    private final RestTemplate restTemplate;

    public RagProxyController() {
        this.restTemplate = new RestTemplate();
    }

    @PostMapping("/query")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<?> queryRag(@RequestBody Map<String, Object> request) {
        try {
            log.info("Proxying RAG query request to: {}/api/v1/qa/answer", ragServiceUrl);

            // Prepare the request for the RAG service
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            // Transform the request to match RAG service expectations
            Map<String, Object> ragRequest = Map.of(
                "question", request.get("query"),
                "include_sources", true,
                "language", "en"
            );

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(ragRequest, headers);

            // Call the RAG service
            ResponseEntity<Map> ragResponse = restTemplate.exchange(
                ragServiceUrl + "/api/v1/qa/answer",
                HttpMethod.POST,
                entity,
                Map.class
            );

            // Transform the response to match frontend expectations
            Map<String, Object> body = ragResponse.getBody();
            Map<String, Object> response = Map.of(
                "answer", body.getOrDefault("answer", ""),
                "sources", body.getOrDefault("sources", new Object[0]),
                "confidence", body.getOrDefault("confidence", 0.0)
            );

            return ResponseEntity.ok(response);

        } catch (HttpClientErrorException e) {
            log.error("Error calling RAG service: {}", e.getMessage());
            return ResponseEntity.status(e.getStatusCode())
                .body(Map.of("error", "RAG service error: " + e.getMessage()));
        } catch (Exception e) {
            log.error("Unexpected error in RAG proxy: ", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to process RAG query"));
        }
    }

    @PostMapping("/search")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<?> searchDocuments(@RequestBody Map<String, Object> request) {
        try {
            String query = (String) request.getOrDefault("query", "");
            Integer limit = (Integer) request.getOrDefault("limit", 10);

            log.info("Proxying search request to RAG service: query={}, limit={}", query, limit);

            // Prepare request for RAG service
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            Map<String, Object> ragRequest = Map.of(
                "query", query,
                "top_k", limit,
                "language", "en"
            );

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(ragRequest, headers);

            // Call RAG service search endpoint
            ResponseEntity<Map> response = restTemplate.exchange(
                ragServiceUrl + "/api/v1/search",
                HttpMethod.POST,
                entity,
                Map.class
            );

            return ResponseEntity.ok(response.getBody());

        } catch (Exception e) {
            log.error("Error in search proxy: ", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to search documents: " + e.getMessage()));
        }
    }

    @GetMapping("/rag-health")
    public ResponseEntity<?> checkRagHealth() {
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(
                ragServiceUrl + "/health", Map.class);
            return ResponseEntity.ok(response.getBody());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                .body(Map.of("status", "RAG service unavailable"));
        }
    }
}