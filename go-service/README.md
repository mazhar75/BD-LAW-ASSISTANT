# Go Service

This directory contains the Go-based background workers for BD Law Assistant.

## Purpose
- Handles concurrent background processing tasks:
  - Document ingestion
  - Indexing
  - Monitoring
- Works alongside the RAG microservice and vector store

## Structure
- `cmd/` - Main entry points for different workers
- `internal/` - Core logic and utilities

## Setup
1. Ensure you have Go 1.19+ installed.
2. Build the service:
   ```
   go build -o bin/go-service ./cmd/...
   ```
3. Run the desired worker:
   ```
   ./bin/go-service
   ```

## Configuration
- Edit environment variables or config files as needed.

## Development
- See the main project README for architecture and integration details. 