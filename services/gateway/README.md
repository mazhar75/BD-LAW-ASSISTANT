# BD Law API Gateway

Central API gateway for Bangladesh Law Assistant providing authentication, authorization, rate limiting, and service routing.

## 🚀 Technology Stack

- **Framework**: Spring Boot 3.2.0
- **Language**: Java 17
- **Security**: Spring Security + JWT (jjwt 0.11.5)
- **Database**: PostgreSQL 14+ (JPA/Hibernate)
- **Caching**: Redis 7+ (rate limiting, sessions)
- **Build Tool**: Maven 3.8+
- **Documentation**: SpringDoc OpenAPI 2.3.0

## ✨ Key Features

### Authentication & Authorization
- JWT-based authentication (access + refresh tokens)
- User registration and login
- Password encryption (BCrypt)
- Token refresh mechanism
- Role-based access control (USER, PREMIUM, ADMIN)

### User Management
- Complete user CRUD operations
- User profile management
- Password change/reset
- Email verification (future)

### Usage Tracking & Analytics
- **UsageTrackingInterceptor**: Tracks all authenticated API calls
- Records endpoint, method, response time, status code
- User-specific usage statistics
- Daily aggregated metrics
- Real-time analytics dashboard data

### Bookmark Management
- Create, read, update, delete bookmarks
- Support for search results, chat citations, law documents
- Folder and tag organization
- Bulk operations (sync, delete)
- User-specific bookmark isolation

### Rate Limiting
- Redis-based distributed rate limiting
- Tiered limits by role:
  - Anonymous: 10 requests/hour
  - User: 100 requests/hour
  - Premium: 1000 requests/hour
  - Admin: Unlimited
- Per-endpoint rate limiting

### Service Routing
- Proxy to RAG service (`/api/rag/*`)
- Proxy to Scraper service (future)
- Request/response transformation
- Error handling and fallbacks

## 📁 Project Structure

```
services/gateway/
├── src/main/java/com/bdlaw/gateway/
│   ├── config/              # Configuration classes
│   │   ├── SecurityConfig.java
│   │   ├── RedisConfig.java
│   │   └── WebConfig.java
│   ├── controller/          # REST controllers
│   │   ├── AuthController.java
│   │   ├── UserController.java
│   │   ├── BookmarkController.java
│   │   ├── RagProxyController.java
│   │   └── ProxyController.java
│   ├── dto/                 # Data Transfer Objects
│   │   ├── LoginRequest.java
│   │   ├── RegisterRequest.java
│   │   ├── BookmarkRequest.java
│   │   └── BookmarkResponse.java
│   ├── entity/              # JPA Entities
│   │   ├── User.java
│   │   ├── UserBookmark.java
│   │   ├── RefreshToken.java
│   │   └── UserUsage.java
│   ├── repository/          # Spring Data repositories
│   │   ├── UserRepository.java
│   │   ├── UserBookmarkRepository.java
│   │   ├── RefreshTokenRepository.java
│   │   └── UserUsageRepository.java
│   ├── service/             # Business logic
│   │   ├── UserService.java
│   │   ├── AuthService.java
│   │   ├── JwtService.java
│   │   ├── UserBookmarkService.java
│   │   └── RateLimitService.java
│   ├── security/            # Security components
│   │   ├── JwtAuthenticationFilter.java
│   │   └── UserDetailsServiceImpl.java
│   ├── interceptor/         # HTTP interceptors
│   │   └── UsageTrackingInterceptor.java
│   ├── filter/              # Servlet filters
│   │   └── RateLimitFilter.java
│   └── util/                # Utility classes
│       └── JwtUtil.java
│
├── src/main/resources/
│   ├── application.properties
│   ├── application-dev.properties
│   ├── application-prod.properties
│   └── db/migration/        # Database migrations
│
├── pom.xml                  # Maven dependencies
└── README.md
```

## 🔧 Environment Variables

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bdlaw
DB_USERNAME=postgres
DB_PASSWORD=your_password

# JWT
JWT_SECRET=your-256-bit-secret-key-minimum-32-characters
JWT_EXPIRATION=3600000
JWT_REFRESH_EXPIRATION=604800000

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Backend Services
RAG_SERVICE_URL=http://localhost:8000
SCRAPER_SERVICE_URL=http://localhost:8001

# Server
SERVER_PORT=8081
```

## 📦 Installation

```bash
cd services/gateway
cp .env.example .env
# Edit .env with your configuration
mvn clean install
```

## 🏃 Running

```bash
# Development
mvn spring-boot:run

# With environment variables
mvn spring-boot:run \
  -Dspring-boot.run.arguments="\
    --DB_PASSWORD=yourpass \
    --JWT_SECRET=your-secret-key"

# Production (JAR)
java -jar target/gateway-1.0.0.jar
```

Access at `http://localhost:8081`

## 🔑 API Endpoints

### Authentication
```
POST   /api/auth/register    - Register new user
POST   /api/auth/login       - Login user
POST   /api/auth/refresh     - Refresh access token
POST   /api/auth/logout      - Logout user
```

### User Management
```
GET    /api/user/me          - Get current user
GET    /api/user/profile     - Get user profile
PUT    /api/user/profile     - Update profile
GET    /api/user/usage       - Get usage statistics
GET    /api/user/usage/daily - Get daily usage
POST   /api/user/change-password
DELETE /api/user/account
```

### Bookmarks
```
POST   /api/bookmarks            - Create bookmark
GET    /api/bookmarks            - List bookmarks
GET    /api/bookmarks/{id}       - Get bookmark
PUT    /api/bookmarks/{id}       - Update bookmark
DELETE /api/bookmarks/{id}       - Delete bookmark
GET    /api/bookmarks/count      - Get count
POST   /api/bookmarks/sync       - Sync bookmarks
```

### RAG Proxy
```
POST   /api/rag/search   - Search laws
POST   /api/rag/query    - Ask question
GET    /api/rag-health   - Health check
```

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE auth.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone_number VARCHAR(20),
    role VARCHAR(20) DEFAULT 'USER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Bookmarks Table
```sql
CREATE TABLE auth.user_bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    item_id VARCHAR(200) NOT NULL,
    bookmark_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    excerpt TEXT,
    category VARCHAR(100),
    url VARCHAR(500),
    tags TEXT[],
    folder_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, item_id)
);
```

### Usage Tracking Table
```sql
CREATE TABLE auth.user_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms BIGINT,
    ip_address VARCHAR(50),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🧪 Testing

```bash
# Run tests
mvn test

# Generate coverage report
mvn test jacoco:report
```

## 🔐 Security Features

- BCrypt password hashing
- JWT token validation
- CORS configuration
- CSRF protection
- Role-based access control
- Rate limiting per user
- SQL injection prevention (JPA)
- XSS protection headers

## 📊 Monitoring

- Spring Boot Actuator endpoints
- Health checks (`/actuator/health`)
- Metrics (`/actuator/metrics`)
- Application logs in `logs/`

