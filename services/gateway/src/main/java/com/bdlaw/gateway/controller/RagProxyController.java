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

    @Value("${rag.service.url:http://localhost:8000}")
    private String ragServiceUrl;

    private final RestTemplate restTemplate;

    public RagProxyController() {
        this.restTemplate = new RestTemplate();
    }

    @PostMapping("/query")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<?> queryRag(@RequestBody Map<String, Object> request) {
        try {
            log.info("Proxying RAG query request to: {}/api/v1/query/api/v1/ask", ragServiceUrl);

            // Prepare the request for the RAG service
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            // Transform the request to match RAG service expectations
            Map<String, Object> ragRequest = Map.of(
                "question", request.get("query"),
                "use_chat_history", true,
                "include_sources", true,
                "language", "en"
            );

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(ragRequest, headers);

            // Call the RAG service - note the double prefix due to router configuration
            ResponseEntity<Map> ragResponse = restTemplate.exchange(
                ragServiceUrl + "/api/v1/query/api/v1/ask",
                HttpMethod.POST,
                entity,
                Map.class
            );

            // Transform the response to match frontend expectations
            Map<String, Object> response = Map.of(
                "answer", ragResponse.getBody().getOrDefault("answer", ""),
                "sources", ragResponse.getBody().getOrDefault("source_documents", new Object[0]),
                "confidence", ragResponse.getBody().getOrDefault("confidence_score", 0.0)
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

    @GetMapping("/search")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<?> searchDocuments(
            @RequestParam String query,
            @RequestParam(defaultValue = "10") int limit) {
        try {
            log.info("Proxying search request to RAG service");

            String url = String.format("%s/api/v1/search?query=%s&k=%d",
                ragServiceUrl, query, limit);

            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);

            return ResponseEntity.ok(response.getBody());

        } catch (Exception e) {
            log.error("Error in search proxy: ", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to search documents"));
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