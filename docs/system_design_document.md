# BD Law Assistant - System Design Document

## Executive Summary

BD Law Assistant is a monolithic RAG-based legal AI system designed to provide intelligent legal assistance for Bangladesh's legal ecosystem. The system combines web crawling, vector search, and AI-powered response generation to deliver accurate legal information in Bengali and English.

## Architecture Overview

### Design Principles
- **Monolithic Architecture**: Single deployable unit with modular components
- **API Gateway Pattern**: Spring Boot gateway as the single entry point
- **Separation of Concerns**: Different technology stacks for specialized tasks
- **Scalability**: Horizontal scaling capabilities through containerization
- **Data Locality**: Local storage with Redis caching for performance

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BD LAW ASSISTANT                            │
│                     Monolithic Architecture                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    FRONTEND LAYER                           │   │
│  │  React 18 + TypeScript + Tailwind CSS                      │   │
│  │  - Responsive SPA                                          │   │
│  │  - JWT Authentication                                      │   │
│  │  - Bengali/English Support                                 │   │
│  └────────────────────────────────────────────────────────────┘   │
│                              ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              API GATEWAY (Spring Boot 3.x)                  │   │
│  │  - Request Routing & Validation                            │   │
│  │  - JWT/OAuth2 Authentication                               │   │
│  │  - Rate Limiting                                           │   │
│  │  - Circuit Breaker Pattern                                 │   │
│  │  - Request/Response Logging                                │   │
│  └────────────────────────────────────────────────────────────┘   │
│                              ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    SERVICE LAYER                            │   │
│  ├─────────────────────────┬──────────────────────────────────┤   │
│  │   Python RAG Service    │    Go Processing Service          │   │
│  │   - FastAPI Framework   │    - Concurrent Processing       │   │
│  │   - LangChain RAG      │    - Document Parsing            │   │
│  │   - Vector Search      │    - Text Chunking               │   │
│  │   - LLM Integration    │    - Data Transformation         │   │
│  └─────────────────────────┴──────────────────────────────────┘   │
│                              ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    DATA LAYER                               │   │
│  ├──────────────┬──────────────┬──────────────┬───────────────┤   │
│  │  PostgreSQL  │    FAISS     │    Redis     │  Local Files  │   │
│  │  - Metadata  │  - Vectors   │  - Cache     │  - Documents  │   │
│  │  - Users     │  - Index     │  - Sessions  │  - Scraped    │   │
│  │  - Queries   │              │  - Rate Limit│    Data       │   │
│  └──────────────┴──────────────┴──────────────┴───────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend Layer (React)

#### Technology Stack
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS for responsive design
- **State Management**: React Context API + Zustand
- **HTTP Client**: Axios with interceptors
- **Form Handling**: React Hook Form
- **Routing**: React Router v6

#### Key Components
```typescript
/frontend
├── /src
│   ├── /components
│   │   ├── SearchBar.tsx         # Main query input
│   │   ├── ChatInterface.tsx     # Q&A conversation UI
│   │   ├── DocumentBrowser.tsx   # Law document explorer
│   │   ├── ResultCard.tsx        # Search result display
│   │   └── AuthForm.tsx          # Login/Register
│   ├── /contexts
│   │   ├── AuthContext.tsx       # JWT management
│   │   └── QueryContext.tsx      # Query state
│   ├── /services
│   │   ├── api.ts               # API client configuration
│   │   └── auth.service.ts      # Authentication service
│   └── /utils
│       ├── bengali.utils.ts     # Bengali text handling
│       └── validation.ts        # Input validation
```

### 2. API Gateway (Spring Boot)

#### Technology Stack
- **Framework**: Spring Boot 3.2
- **Security**: Spring Security with JWT
- **Database**: Spring Data JPA
- **Caching**: Spring Cache with Redis
- **Documentation**: SpringDoc OpenAPI
- **Monitoring**: Spring Actuator

#### Package Structure
```java
/api-gateway
├── /src/main/java/com/bdlaw/gateway
│   ├── /config
│   │   ├── SecurityConfig.java      # JWT & OAuth2 config
│   │   ├── RedisConfig.java         # Cache configuration
│   │   ├── CorsConfig.java          # CORS settings
│   │   └── RateLimitConfig.java     # Rate limiting
│   ├── /controllers
│   │   ├── AuthController.java      # Authentication endpoints
│   │   ├── QueryController.java     # RAG query proxy
│   │   ├── DocumentController.java  # Document management
│   │   └── UserController.java      # User management
│   ├── /services
│   │   ├── RagProxyService.java    # Python service integration
│   │   ├── AuthService.java        # JWT generation/validation
│   │   ├── RateLimitService.java   # Request throttling
│   │   └── CacheService.java       # Redis cache management
│   ├── /filters
│   │   ├── JwtAuthFilter.java      # JWT validation filter
│   │   └── LoggingFilter.java      # Request/Response logging
│   └── /models
│       ├── User.java                # User entity
│       ├── Query.java               # Query history
│       └── ApiResponse.java        # Standard response wrapper
```

#### API Endpoints
```yaml
Authentication:
  POST /api/auth/register    # User registration
  POST /api/auth/login       # User login
  POST /api/auth/refresh     # Token refresh
  GET  /api/auth/logout      # Logout

Query Service:
  POST /api/query/search     # Semantic search
  POST /api/query/ask        # RAG Q&A
  GET  /api/query/history    # User query history

Documents:
  GET  /api/documents/browse # Browse laws
  GET  /api/documents/{id}   # Get specific law
  POST /api/documents/search # Full-text search

User Management:
  GET  /api/user/profile     # Get profile
  PUT  /api/user/profile     # Update profile
  GET  /api/user/preferences # Get preferences
```

### 3. Python RAG Service

#### Technology Stack
- **Framework**: FastAPI with async support
- **RAG**: LangChain for orchestration
- **Embeddings**: Sentence Transformers (multilingual)
- **Vector Store**: FAISS for local indexing
- **LLM**: OpenAI GPT-4 / Claude / Local models
- **Web Scraping**: Firecrawl API

#### Module Structure
```python
/rag-service
├── /app
│   ├── /api
│   │   ├── endpoints.py          # FastAPI routes
│   │   └── middleware.py         # Request validation
│   ├── /core
│   │   ├── config.py            # Configuration
│   │   ├── embeddings.py        # Embedding generation
│   │   ├── vector_store.py      # FAISS operations
│   │   └── llm_client.py        # LLM integration
│   ├── /services
│   │   ├── rag_service.py       # RAG pipeline
│   │   ├── crawler_service.py   # Firecrawl integration
│   │   ├── chunking_service.py  # Text chunking
│   │   └── citation_service.py  # Citation extraction
│   ├── /models
│   │   ├── query.py             # Query models
│   │   └── document.py          # Document models
│   └── /utils
│       ├── bengali_nlp.py       # Bengali processing
│       └── text_cleaner.py      # Text preprocessing
```

#### RAG Pipeline
```python
# Core RAG workflow
1. Query Processing
   - Language detection (Bengali/English)
   - Query expansion and reformulation
   - Intent classification

2. Document Retrieval
   - Embedding generation
   - FAISS similarity search (k=10)
   - Reranking with cross-encoder

3. Context Assembly
   - Chunk aggregation
   - Metadata enrichment
   - Citation extraction

4. Response Generation
   - Prompt engineering
   - LLM inference
   - Response formatting
   - Citation linking
```

### 4. Go Processing Service

#### Purpose
High-performance concurrent processing for:
- Document parsing and extraction
- Bulk text processing
- Data transformation
- Background job processing

#### Structure
```go
/go-service
├── /cmd
│   └── server/main.go           # Entry point
├── /internal
│   ├── /handlers
│   │   ├── document.go          # Document processing
│   │   └── crawler.go           # Crawling coordination
│   ├── /services
│   │   ├── parser.go            # HTML/PDF parsing
│   │   ├── chunker.go           # Text chunking
│   │   └── processor.go         # Concurrent processing
│   └── /models
│       ├── document.go          # Document models
│       └── task.go              # Processing tasks
```

### 5. Data Layer

#### PostgreSQL Schema
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Laws table
CREATE TABLE laws (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    act_name VARCHAR(500) NOT NULL,
    act_number VARCHAR(100),
    year INTEGER,
    chapter VARCHAR(100),
    section VARCHAR(100),
    content TEXT NOT NULL,
    content_bengali TEXT,
    metadata JSONB,
    source_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Embeddings table
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    law_id UUID REFERENCES laws(id),
    chunk_index INTEGER,
    chunk_text TEXT,
    vector_id VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Query history table
CREATE TABLE query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    query TEXT NOT NULL,
    query_type VARCHAR(50),
    response TEXT,
    citations JSONB,
    confidence_score FLOAT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_laws_act_name ON laws(act_name);
CREATE INDEX idx_laws_year ON laws(year);
CREATE INDEX idx_laws_metadata ON laws USING GIN(metadata);
CREATE INDEX idx_query_history_user ON query_history(user_id);
CREATE INDEX idx_query_history_created ON query_history(created_at);
```

#### FAISS Vector Storage
```python
# Vector index configuration
index_config = {
    "dimension": 768,  # Multilingual BERT dimension
    "index_type": "IVF4096,Flat",  # Inverted file index
    "metric": "cosine",  # Similarity metric
    "nprobe": 10,  # Search parameter
    "chunk_size": 512,  # Text chunk size
    "overlap": 50  # Chunk overlap
}
```

#### Redis Cache Structure
```yaml
Cache Keys:
  query:{hash}           # Cached query results (TTL: 1 hour)
  user:session:{id}      # User sessions (TTL: 24 hours)
  rate:limit:{ip}        # Rate limiting (TTL: 1 minute)
  doc:embed:{id}         # Document embeddings (TTL: 7 days)
```

#### Local File Storage
```
/data
├── /scraped           # Raw scraped HTML/PDF files
│   ├── /laws
│   ├── /cases
│   └── /regulations
├── /processed         # Cleaned and structured data
│   ├── /json
│   └── /markdown
├── /indexes          # FAISS index files
│   ├── laws.index
│   └── cases.index
└── /backups          # Database backups
```

## Data Flow Diagrams

### 1. Query Processing Flow
```
User Query → API Gateway → Rate Check → Auth Validation
    ↓
Cache Check (Redis)
    ↓ (cache miss)
Python RAG Service
    ↓
Query Processing → Embedding → Vector Search (FAISS)
    ↓
Context Retrieval (PostgreSQL)
    ↓
LLM Processing → Response Generation
    ↓
Cache Update → Response → API Gateway → User
```

### 2. Document Ingestion Flow
```
Firecrawl API → Raw HTML/PDF
    ↓
Go Service (Concurrent Processing)
    ↓
Parse → Clean → Chunk → Metadata Extract
    ↓
PostgreSQL (Store) + Python Service (Embed)
    ↓
FAISS Index Update
```

## Security Architecture

### Authentication & Authorization
- **JWT Tokens**: RS256 algorithm with 24-hour expiry
- **OAuth2**: Support for Google/GitHub login
- **Role-Based Access**: Admin, User, Guest roles
- **Session Management**: Redis-backed sessions

### API Security
```java
// Spring Security Configuration
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    // JWT validation
    // CORS configuration
    // CSRF protection (disabled for APIs)
    // Rate limiting per IP/User
    // SQL injection prevention
    // XSS protection headers
}
```

### Data Security
- **Encryption at Rest**: Database encryption
- **Encryption in Transit**: TLS 1.3 for all connections
- **Sensitive Data**: Bcrypt for passwords
- **API Keys**: Environment variables
- **Audit Logging**: All data access logged

## Performance Optimization

### Caching Strategy
1. **Query Cache**: Redis with 1-hour TTL
2. **Embedding Cache**: Local memory + Redis
3. **Static Assets**: CDN for frontend
4. **Database**: Query result caching

### Scaling Approach
1. **Horizontal Scaling**: Container orchestration
2. **Load Balancing**: Nginx reverse proxy
3. **Database**: Read replicas for queries
4. **Vector Search**: Distributed FAISS

### Performance Targets
- **Response Time**: < 2 seconds for queries
- **Throughput**: 100 concurrent users
- **Availability**: 99.9% uptime
- **Vector Search**: < 100ms for 1M documents

## Deployment Architecture

### Docker Composition
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: bdlaw
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  api-gateway:
    build: ./api-gateway
    ports:
      - "8080:8080"
    depends_on:
      - postgres
      - redis
    environment:
      SPRING_PROFILES_ACTIVE: production

  rag-service:
    build: ./rag-service
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}

  go-service:
    build: ./go-service
    ports:
      - "8001:8001"

  frontend:
    build: ./frontend
    ports:
      - "3000:80"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api-gateway
      - frontend

volumes:
  postgres_data:
  redis_data:
```

### Infrastructure Requirements
```yaml
Development:
  CPU: 4 cores
  RAM: 8GB
  Storage: 50GB SSD

Production:
  CPU: 8 cores
  RAM: 32GB
  Storage: 200GB SSD
  GPU: Optional (for local LLM)
```

## Monitoring & Observability

### Metrics Collection
- **Application Metrics**: Spring Actuator + Prometheus
- **System Metrics**: Node Exporter
- **Custom Metrics**: Query latency, cache hit rate

### Logging
```yaml
Logging Levels:
  - ERROR: System failures
  - WARN: Performance issues
  - INFO: User actions, API calls
  - DEBUG: Detailed execution flow

Log Aggregation:
  - ELK Stack (Elasticsearch, Logstash, Kibana)
  - Structured JSON logging
  - Correlation IDs for request tracing
```

### Health Checks
```yaml
Endpoints:
  /health         # Basic health
  /health/ready   # Readiness probe
  /health/live    # Liveness probe
  /metrics        # Prometheus metrics
```

## API Documentation

### OpenAPI Specification
```yaml
openapi: 3.0.0
info:
  title: BD Law Assistant API
  version: 1.0.0
paths:
  /api/query/search:
    post:
      summary: Semantic search for legal documents
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                query:
                  type: string
                language:
                  type: string
                  enum: [bn, en]
                limit:
                  type: integer
                  default: 10
```

## Testing Strategy

### Test Coverage
```yaml
Unit Tests:
  - Service layer: 80% coverage
  - Controllers: 70% coverage
  - Utils: 90% coverage

Integration Tests:
  - API endpoints
  - Database operations
  - Cache operations

E2E Tests:
  - User workflows
  - Query processing
  - Authentication flow

Performance Tests:
  - Load testing (JMeter)
  - Stress testing
  - Vector search benchmarks
```

## Development Workflow

### Git Structure
```
main
├── develop
├── feature/[feature-name]
├── bugfix/[bug-name]
└── release/[version]
```

### CI/CD Pipeline
```yaml
Pipeline Stages:
  1. Code Analysis (SonarQube)
  2. Unit Tests
  3. Build Docker Images
  4. Integration Tests
  5. Security Scan
  6. Deploy to Staging
  7. E2E Tests
  8. Deploy to Production
```

## Disaster Recovery

### Backup Strategy
- **Database**: Daily automated backups
- **Vector Indexes**: Weekly snapshots
- **Documents**: Version controlled in S3
- **Configuration**: Git repository

### Recovery Procedures
```yaml
RTO: 4 hours  # Recovery Time Objective
RPO: 1 hour   # Recovery Point Objective

Procedures:
  1. Database restoration from backup
  2. Vector index rebuild from documents
  3. Cache warming
  4. Service health validation
```

## Future Enhancements

### Phase 2 Features
1. **Voice Interface**: Speech-to-text for queries
2. **Mobile Apps**: iOS/Android native apps
3. **Advanced Analytics**: Usage patterns, query trends
4. **Multi-tenancy**: Organization-specific deployments
5. **Offline Mode**: Local-first architecture

### Technical Improvements
1. **GraphQL API**: Alternative to REST
2. **Kubernetes**: Container orchestration
3. **ML Pipeline**: Custom model fine-tuning
4. **Real-time Updates**: WebSocket for live data
5. **Federated Search**: Multiple data sources

## Conclusion

This system design provides a robust, scalable foundation for the BD Law Assistant platform. The monolithic architecture with modular components ensures maintainability while allowing for future microservices migration if needed. The combination of Spring Boot API Gateway, Python RAG service, and Go processing service leverages each technology's strengths for optimal performance and functionality.

## Appendix

### A. Technology Justification

| Component | Technology | Justification |
|-----------|-----------|--------------|
| API Gateway | Spring Boot | Enterprise-grade, robust security, excellent monitoring |
| RAG Service | Python/FastAPI | Rich AI/ML ecosystem, LangChain support |
| Processing | Go | Superior concurrency for bulk operations |
| Frontend | React | Component reusability, large ecosystem |
| Vector DB | FAISS | Local deployment, cost-effective |
| Cache | Redis | Industry standard, persistent cache |
| Database | PostgreSQL | ACID compliance, JSON support |

### B. Compliance & Legal Considerations

- **Data Privacy**: GDPR-compliant data handling
- **Legal Accuracy**: Disclaimer on AI-generated advice
- **Audit Trail**: Complete query logging
- **Data Retention**: 90-day query history
- **Terms of Service**: Clear usage guidelines

### C. Cost Estimation (Monthly)

```yaml
Development Environment:
  Infrastructure: $100
  APIs (OpenAI): $50
  Total: $150/month

Production Environment:
  Infrastructure (AWS): $500
  APIs (OpenAI): $300
  CDN: $50
  Monitoring: $100
  Backups: $50
  Total: $1000/month
```

### D. Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|---------|------------|
| API Rate Limits | Medium | High | Caching, request queuing |
| LLM Hallucination | Low | High | Citation verification |
| Data Breach | Low | Critical | Encryption, access control |
| Service Downtime | Medium | High | Redundancy, health checks |
| Scalability Issues | Medium | Medium | Horizontal scaling ready |

---

*Document Version: 1.0*
*Last Updated: 2025-09-17*
*Prepared for: BD Law Assistant Team*