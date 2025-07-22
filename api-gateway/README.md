# API Gateway

This directory contains the Java Spring Boot API Gateway for BD Law Assistant.

## Purpose
- Handles authentication, routing, and logging for all API requests
- Acts as the main entry point for frontend and external clients
- Forwards requests to backend microservices (RAG, Go service, etc.) via REST/gRPC

## Structure
- `src/` - Main source code for the Spring Boot application

## Setup
1. Ensure you have Java 17+ and Maven installed.
2. Build the project:
   ```
   mvn clean install
   ```
3. Run the API Gateway:
   ```
   mvn spring-boot:run
   ```

## Configuration
- Edit `application.properties` for service endpoints, authentication, etc.

## Development
- See the main project README for architecture and integration details. 