# BD Law Assistant

AI-powered legal information system for Bangladesh providing intelligent search and question-answering across 300+ laws with 29,000+ indexed document chunks.

## ✨ Key Features

- **AI-Powered Legal Search** - Semantic search across Bangladesh laws
- **Intelligent Q&A** - Natural language legal questions with citations
- **User Dashboard & Analytics** - Real-time usage statistics and insights
- **Bookmark Management** - Backend-synced bookmark system
- **Bilingual Support** - Full English and Bengali language support
- **JWT Authentication** - Secure authentication with automatic token refresh
- **Role-Based Access Control** - User, Premium, and Admin tiers
- **Usage Tracking** - Comprehensive user activity analytics
- **Modern Web Interface** - Responsive Next.js frontend
- **Microservices Architecture** - Scalable, maintainable design

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BD Law Assistant                            │
│                  AI-Powered Legal Information System                │
└─────────────────────────────────────────────────────────────────────┘

                            USER INTERFACE
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend Service                            │
│                    Next.js 15 + React 19 + TS                       │
│                         Port: 3000                                  │
│                                                                     │
│  Features:                                                          │
│  • Bilingual UI (EN/BN)          • Search Interface                 │
│  • User Authentication           • Chat Interface (Perplexity-style)│
│  • Bookmarks (localStorage)      • Responsive Design                 │
└──────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ HTTP + JWT Token
                              │
                              ▼
                      API GATEWAY LAYER
┌─────────────────────────────────────────────────────────────────────┐
│                         Gateway Service                             │
│                  Spring Boot 3.2 + Java 17                          │
│                         Port: 8081                                  │
│                                                                     │
│  Responsibilities:                                                  │
│  • Authentication & Authorization     • JWT Token Management        │
│  • Rate Limiting (Redis)              • Request Routing             │
│  • User Management (PostgreSQL)       • Security & CORS             │
│  • Audit Logging                      • Role-Based Access Control   │
└──────────┬───────────────────────┬────────────────────┬─────────────┘
           │                       │                    │
           │                       │                    │
           ▼                       ▼                    ▼
    BACKEND SERVICES LAYER
┌──────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   RAG Service    │    │ Scraper Service  │    │ Future Services │
│   FastAPI +      │    │   Flask +        │    │                 │
│   Python 3.11    │    │   Python 3.11    │    │  • Analytics    │
│   Port: 8000     │    │   Port: 8001     │    │  • Notifications│
│                  │    │                  │    │  • ML Training  │
│  Features:       │    │  Features:       │    │                 │
│  • Vector Search │    │  • Web Scraping  │    │                 │
│  • Semantic      │    │  • Firecrawl API │    │                 │
│  • Keyword       │    │  • Redis Queue   │    │                 │
│  • Hybrid Search │    │  • Web UI        │    │                 │
│  • RAG Q&A       │    │  • Bilingual     │    │                 │
│  • Gemini LLM    │    │                  │    │                 │
└────────┬─────────┘    └────────┬─────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
                   DATA LAYER
┌─────────────────────────────────────────────────────────────────────┐
│                         PostgreSQL Database                         │
│                            Port: 5432                               │
│                                                                     │
│  ┌──────────────────┐              ┌──────────────────┐             │
│  │   Auth Schema    │              │  Public Schema   │             │
│  │  (Gateway Owned) │              │  (RAG Owned)     │             │
│  │                  │              │                  │             │
│  │  • users         │              │  • laws (300+)   │             │
│  │  • roles         │              │  • law_chunks    │             │
│  │  • user_roles    │              │    (29,219)      │             │
│  │  • api_keys      │              │  • embeddings    │             │
│  │  • refresh_tokens│              │  • query_logs    │             │
│  │  • audit_logs    │              │                  │             │
│  │  • rate_limits   │              │                  │             │
│  └──────────────────┘              └──────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                           Redis Cache                               │
│                           Port: 6379                                │
│                                                                     │
│  • Rate Limiting Counters        • Session Cache                    │
│  • Scraper Task Queue            • Temporary Data                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    ChromaDB Vector Store                            │
│                         (Embedded)                                  │
│                                                                     │
│  • 29,219 Law Chunk Vectors                                         │
│  • 384-dimensional embeddings                                       │
│  • Cosine similarity search                                         │
│  • Model: paraphrase-multilingual-MiniLM-L12-v2                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       External Services                             │
│                                                                     │
│  • Google Gemini API (LLM)       • Firecrawl API (Web Scraping)     │
└─────────────────────────────────────────────────────────────────────┘
```

## 📦 Services

### Frontend (`services/frontend`)
- **Tech**: Next.js 15.5.3, React 19, TypeScript, Tailwind CSS 4
- **Features**: User dashboard, search, chat, bookmarks, analytics
- **Port**: 3000

### Gateway (`services/gateway`)
- **Tech**: Spring Boot 3.2, Java 17, PostgreSQL, Redis
- **Features**: JWT auth, user management, bookmarks, usage tracking, rate limiting
- **Port**: 8081

### RAG Service (`services/rag_service`)
- **Tech**: Python 3.11, FastAPI, ChromaDB, Gemini 2.5 Flash
- **Features**: Vector search, semantic search, AI Q&A
- **Port**: 8000

### Scraper (`services/scraper`)
- **Tech**: Python 3.11, Firecrawl API, Redis
- **Features**: Automated legal document scraping
- **Port**: 8001

## 🚀 Quick Start

### Prerequisites
- Node.js 20+, Python 3.11+, Java 17+
- PostgreSQL 14+, Redis 7+
- Gemini API Key

### Installation

```bash
# 1. Start PostgreSQL and Redis
redis-server

# 2. Start RAG Service
cd services/rag_service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with GEMINI_API_KEY and DB_PASSWORD
python src/main.py

# 3. Start Gateway
cd services/gateway
cp .env.example .env
# Edit .env with DB_PASSWORD and JWT_SECRET
mvn spring-boot:run

# 4. Start Frontend
cd services/frontend
npm install
cp .env.example .env.local
# Edit .env.local with NEXT_PUBLIC_GATEWAY_URL
npm run dev
```

Access at `http://localhost:3000`

## 📊 Database Schema

### PostgreSQL Tables
```sql
-- Users and Authentication
auth.users (id, username, email, password_hash, role, ...)
auth.refresh_tokens (id, user_id, token, expires_at, ...)

-- Bookmarks
auth.user_bookmarks (id, user_id, item_id, title, type, ...)

-- Usage Tracking
auth.user_usage (id, user_id, endpoint, method, response_time_ms, date, ...)

-- Legal Documents
public.laws (id, title, content, category, ...)
public.law_chunks (id, law_id, chunk_text, embedding, ...)
```

## 🔐 Security

- BCrypt password hashing
- JWT with access (15min) + refresh (7 days) tokens
- Redis-based rate limiting by role
- CORS and CSRF protection
- SQL injection prevention (JPA)
- XSS protection headers

## 📈 Current Status

✅ **Production Ready**
- 300+ laws indexed
- 29,219 document chunks
- Full authentication system
- User analytics dashboard
- Backend-synced bookmarks
- Real-time usage tracking
- Working login/logout
- All core features implemented

## 📖 Documentation

- [Frontend README](services/frontend/README.md)
- [Gateway README](services/gateway/README.md)
- [RAG Service README](services/rag_service/README.md)
- [Scraper README](services/scraper/README.md)
- [Architecture Summary](ARCHITECTURE_SUMMARY.md)
- [Documentation Index](DOCUMENTATION_INDEX.md)

## 🧪 Testing

```bash
# Gateway tests
cd services/gateway
mvn test

# RAG Service tests
cd services/rag_service
pytest

# Frontend linting
cd services/frontend
npm run lint
```

## 🚢 Deployment

See individual service READMEs for deployment instructions.

**Docker Compose** (recommended):
```bash
docker-compose up -d
```

