# BD Law API Gateway

## Overview

The API Gateway is the central entry point for the Bangladesh Law Assistant microservices ecosystem. Built with Spring Boot 3.2, it provides authentication, authorization, rate limiting, and intelligent routing to backend services including RAG, Scraper, and future microservices.

## Features

- **JWT Authentication** - Secure token-based authentication with access and refresh tokens
- **User Management** - Registration, login, email verification, and password reset
- **Rate Limiting** - Redis-based tiered rate limiting (Anonymous, User, Premium, Admin)
- **Request Routing** - Intelligent proxy routing to backend microservices
- **Role-Based Access Control** - Fine-grained permissions (USER, ADMIN, PREMIUM)
- **CORS Support** - Configurable cross-origin resource sharing
- **Health Monitoring** - Spring Actuator endpoints for monitoring
- **API Documentation** - OpenAPI/Swagger UI at `/swagger-ui.html`

## Architecture

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     ↓
┌──────────────────────────────────────┐
│   API Gateway (Port 8081)            │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  Security Filter Chain         │ │
│  │  • JWT Authentication          │ │
│  │  • Rate Limiting (Redis)       │ │
│  │  • CORS Validation             │ │
│  │  • Request Logging             │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
     │
     ├──────────────────┬──────────────────┐
     ↓                  ↓                  ↓
┌─────────┐      ┌─────────┐      ┌─────────┐
│   RAG   │      │ Scraper │      │ Future  │
│ Service │      │ Service │      │Services │
│  :8000  │      │  :8001  │      │         │
└─────────┘      └─────────┘      └─────────┘
```

### Component Interactions

1. **Client Request** → Gateway receives HTTP request
2. **Authentication** → JWT token validated (if required)
3. **Rate Limiting** → Redis checks request count
4. **Authorization** → Role-based access control applied
5. **Routing** → Request proxied to appropriate backend service
6. **Response** → Service response returned to client with headers

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Spring Boot | 3.2.0 |
| Language | Java | 17+ |
| Build Tool | Maven | 3.8+ |
| Security | Spring Security + JWT | jjwt 0.11.5 |
| Database | PostgreSQL | 14+ |
| Cache | Redis | 7+ |
| Documentation | SpringDoc OpenAPI | 2.3.0 |
| Monitoring | Micrometer + Prometheus | - |

## Prerequisites

- **Java 17+** - JDK installed and configured
- **Maven 3.8+** - Build tool
- **PostgreSQL 14+** - For user data and sessions
- **Redis 7+** - For rate limiting and caching
- **RAG Service** - Running on port 8000 (for proxying)

## Installation

### 1. Database Setup

```bash
# Start PostgreSQL and create database
psql -U postgres

CREATE DATABASE bdlaw;

# Run schema initialization
psql -U postgres -d bdlaw -f src/main/resources/schema.sql
```

### 2. Redis Setup

```bash
# Option 1: Native Redis
redis-server --port 6379

# Option 2: Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### 3. Configuration

Copy the environment template:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Database
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT Secret (generate with: openssl rand -base64 64)
JWT_SECRET=your-256-bit-secret-key

# Service URLs
RAG_SERVICE_URL=http://localhost:8000
```

### 4. Build

```bash
cd services/gateway
mvn clean package
```

### 5. Run

```bash
# Using Maven
mvn spring-boot:run -Dspring-boot.run.arguments="\
  --DB_PASSWORD=your_password \
  --JWT_SECRET=your_secret \
  --RAG_SERVICE_URL=http://localhost:8000"

# Or using JAR
java -jar target/gateway-1.0.0.jar \
  --DB_PASSWORD=your_password \
  --JWT_SECRET=your_secret
```

The gateway starts on **http://localhost:8081**

## API Endpoints

### Public Endpoints

#### Health Check
```http
GET /actuator/health
```

Returns gateway health status including database and Redis connectivity.

#### User Registration
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "fullName": "John Doe"
}
```

**Response:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiJ9...",
  "tokenType": "Bearer",
  "expiresIn": 86400,
  "user": {
    "id": 1,
    "username": "johndoe",
    "roles": ["ROLE_USER"]
  }
}
```

#### User Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Note:** Currently has a known issue (401 Unauthorized) - requires security configuration update.

### Protected Endpoints

All protected endpoints require the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

#### Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refreshToken": "eyJhbGciOiJIUzI1NiJ9..."
}
```

#### RAG Service Proxy

The gateway proxies requests to the RAG service at `/api/rag/**`:

**Search (Public)**
```http
POST /api/rag/search
Content-Type: application/json

{
  "query": "property law in Bangladesh",
  "limit": 5
}
```

**Q&A (Protected)**
```http
POST /api/rag/qa
Authorization: Bearer <token>
Content-Type: application/json

{
  "question": "What are the property rights?"
}
```

### Rate Limiting

All responses include rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1759420000
```

**Default Limits:**
- Anonymous: 10 requests/minute
- Authenticated: 100 requests/minute
- Premium: 1000 requests/minute

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_USER` | PostgreSQL username | postgres | No |
| `DB_PASSWORD` | PostgreSQL password | - | Yes |
| `REDIS_HOST` | Redis server host | localhost | No |
| `REDIS_PORT` | Redis server port | 6379 | No |
| `JWT_SECRET` | JWT signing secret | - | Yes |
| `JWT_EXPIRATION` | Access token expiry (ms) | 86400000 | No |
| `JWT_REFRESH_EXPIRATION` | Refresh token expiry (ms) | 604800000 | No |
| `RAG_SERVICE_URL` | RAG service URL | http://localhost:8000 | No |
| `RATE_LIMIT_ANONYMOUS` | Anonymous rate limit | 10 | No |
| `RATE_LIMIT_AUTHENTICATED` | User rate limit | 100 | No |
| `RATE_LIMIT_PREMIUM` | Premium rate limit | 1000 | No |

### Application Properties

Key configuration in `src/main/resources/application.yml`:

```yaml
server:
  port: 8081

spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/bdlaw
    username: ${DB_USER:postgres}
    password: ${DB_PASSWORD}

  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}

  cloud:
    gateway:
      routes:
        - id: rag-service
          uri: ${RAG_SERVICE_URL:http://localhost:8000}
          predicates:
            - Path=/api/rag/**
          filters:
            - StripPrefix=2
            - RateLimit

jwt:
  secret: ${JWT_SECRET}
  expiration: ${JWT_EXPIRATION:86400000}
  refresh-expiration: ${JWT_REFRESH_EXPIRATION:604800000}
```

## Monitoring

### Actuator Endpoints

```bash
# Health status
GET /actuator/health

# Application metrics
GET /actuator/metrics

# Prometheus metrics
GET /actuator/prometheus

# All available endpoints
GET /actuator
```

### API Documentation

Access Swagger UI for interactive API documentation:

```
http://localhost:8081/swagger-ui.html
```

## Project Structure

```
services/gateway/
├── src/
│   ├── main/
│   │   ├── java/com/bdlaw/gateway/
│   │   │   ├── config/              # Configuration classes
│   │   │   │   ├── SecurityConfig.java
│   │   │   │   ├── RedisConfig.java
│   │   │   │   └── WebClientConfig.java
│   │   │   ├── controller/          # REST controllers
│   │   │   │   ├── AuthController.java
│   │   │   │   └── UserController.java
│   │   │   ├── dto/                 # Data transfer objects
│   │   │   ├── entity/              # JPA entities
│   │   │   │   ├── User.java
│   │   │   │   └── Role.java
│   │   │   ├── repository/          # Spring Data repositories
│   │   │   ├── security/            # Security components
│   │   │   │   ├── JwtAuthenticationFilter.java
│   │   │   │   └── JwtTokenProvider.java
│   │   │   ├── service/             # Business logic
│   │   │   │   ├── AuthService.java
│   │   │   │   └── UserService.java
│   │   │   └── GatewayApplication.java
│   │   └── resources/
│   │       ├── application.yml      # Main configuration
│   │       └── schema.sql           # Database schema
│   └── test/
│       └── java/                    # Unit & integration tests
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore rules
├── Dockerfile                       # Docker image definition
├── pom.xml                          # Maven dependencies
└── README.md
```

## Security

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### JWT Tokens

- **Access Token**: Short-lived (24 hours default)
- **Refresh Token**: Long-lived (7 days default)
- **Algorithm**: HMAC-SHA256 (HS256)

### Security Headers

The gateway automatically adds security headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

## Testing

### Manual Testing

```bash
# Test health
curl http://localhost:8081/actuator/health

# Test registration
curl -X POST http://localhost:8081/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!",
    "fullName": "Test User"
  }'

# Test RAG search
curl -X POST http://localhost:8081/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "property law", "limit": 5}'
```

### Automated Tests

Run the test suite:

```bash
# Unit tests
mvn test

# Integration tests
mvn verify

# Full test suite with report
python test_gateway_endpoints.py
```

See `docs/GATEWAY_TEST_REPORT.md` for detailed test results.

## Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Verify database exists
psql -U postgres -l | grep bdlaw

# Test connection
psql -U postgres -d bdlaw -c "SELECT version();"
```

**Redis Connection Error**
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Check Redis info
redis-cli info server
```

**Port Already in Use**
```bash
# Find process using port 8081
netstat -ano | findstr :8081

# Kill process (Windows)
taskkill /PID <pid> /F

# Or change port in application.yml
server.port: 8082
```

**JWT Token Invalid**
- Ensure `JWT_SECRET` is consistent across restarts
- Check system time synchronization
- Verify token hasn't expired

### Known Issues

1. **Login Endpoint 401 Error** - Login endpoint currently blocked by authentication filter. Requires `SecurityConfig.java` update to whitelist `/api/auth/login`.

2. **Gateway Latency** - Adds ~800ms overhead vs direct service access. Consider connection pooling and caching for production.

See full analysis in `docs/GATEWAY_TEST_REPORT.md`.

## Deployment

### Docker

```bash
# Build image
docker build -t bd-law-gateway:1.0.0 .

# Run container
docker run -d \
  -p 8081:8081 \
  -e DB_PASSWORD=your_password \
  -e JWT_SECRET=your_secret \
  --name gateway \
  bd-law-gateway:1.0.0
```

### Docker Compose

See root `docker-compose.yml` for full stack deployment with all services.

## Development

### Adding New Service Routes

Edit `application.yml`:

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: new-service
          uri: http://localhost:9000
          predicates:
            - Path=/api/new-service/**
          filters:
            - StripPrefix=2
            - name: RateLimit
              args:
                redis-rate-limiter.replenishRate: 100
                redis-rate-limiter.burstCapacity: 200
```

### Running Tests

```bash
# Run all tests
mvn test

# Run specific test class
mvn test -Dtest=AuthControllerTest

# Generate coverage report
mvn jacoco:report
```

## License

Apache License 2.0

## Support

- **Documentation**: `docs/GATEWAY_TEST_REPORT.md`
- **Test Suite**: `test_gateway_endpoints.py`
- **Issues**: GitHub Issues

---

**Version**: 1.0.0
**Status**: Operational
**Last Updated**: 2025-10-02
