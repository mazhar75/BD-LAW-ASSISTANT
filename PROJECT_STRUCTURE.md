# BD Law Assistant - Project Structure

## 📁 Clean Architecture (Post-Refactoring)

```
BD Law Assistant/
│
├── 📁 services/                    # Microservices
│   ├── 📁 scraper/                # ✅ Data scraping service (Phase 1 Complete)
│   │   ├── 📁 scrapers/          # Core scraping modules
│   │   │   ├── 📁 config/        # Configuration management
│   │   │   ├── 📁 core/          # Firecrawl, Queue, Data validation
│   │   │   ├── 📁 storage/       # File storage handlers
│   │   │   ├── 📁 utils/         # Logging utilities
│   │   │   ├── 📁 validators/    # Content validators
│   │   │   ├── bd_law_crawler.py # Main crawler orchestrator
│   │   │   └── scheduler.py      # Automated scheduled tasks
│   │   ├── 📁 templates/         # Web UI templates
│   │   ├── web_crawler_app.py    # Flask web interface
│   │   └── requirements.txt      # Python dependencies
│   │
│   ├── 📁 rag/                   # 🚧 RAG service (Phase 2 - Next)
│   ├── 📁 gateway/               # 📋 API Gateway (Phase 3)
│   └── 📁 frontend/              # 📋 React frontend (Phase 4)
│
├── 📁 shared/                    # Shared components
│   ├── 📁 models/               # Shared data models
│   └── 📁 utils/                # Common utilities
│
├── 📁 infrastructure/            # Infrastructure configuration
│   ├── 📁 docker/              # Docker configurations
│   │   └── Dockerfile.scraper  # Scraper service container
│   └── 📁 k8s/                 # Kubernetes (future)
│
├── 📁 data/                     # Data storage
│   ├── 📁 raw/                 # Scraped raw data
│   │   ├── 📁 acts/           # English acts (markdown + metadata)
│   │   ├── 📁 volumes/        # Legal volumes
│   │   └── 📁 bengali/        # Bengali content
│   ├── 📁 processed/           # Processed/indexed data
│   └── 📁 logs/               # Application logs
│
├── 📁 docs/                    # Documentation
│   ├── 📁 archive/            # Archived old docs
│   ├── mvp_implementation_plan.md
│   └── system_design_document.md
│
├── 📄 docker-compose.yml       # Service orchestration
├── 📄 start_services.sh        # Startup script
├── 📄 ARCHITECTURE.md          # Architecture documentation
├── 📄 README.md                # Main project README
└── 📄 .env                    # Environment variables
```

## ✅ Refactoring Completed

### What Changed:
1. **Clean Service Architecture**: Moved from monolithic to service-based structure
2. **Organized Scraper**: All scraper code now under `services/scraper/`
3. **Infrastructure Separation**: Docker configs moved to `infrastructure/`
4. **Documentation Cleanup**: Archived redundant docs, kept essential ones
5. **Fixed Dependencies**: Created missing `scheduler.py`
6. **Updated Configurations**: Docker Compose and startup scripts updated

### Services Status:
- ✅ **Scraper Service**: Fully operational with 100+ acts scraped
- 🚧 **RAG Service**: Next implementation (Phase 2)
- 📋 **API Gateway**: Planned (Phase 3)
- 📋 **Frontend**: Planned (Phase 4)

## 🚀 Quick Start

### Using Docker:
```bash
docker-compose up -d
# Access web UI at http://localhost:5000
```

### Local Development:
```bash
# Start Redis
redis-server --port 6379

# Run scraper
cd services/scraper
python scrapers/bd_law_crawler.py --test

# Run web UI
python web_crawler_app.py
```

## 📊 Data Flow

```
Web Scraping (Firecrawl) → Redis Queue → Processing → File Storage
                                ↓
                        [Future: PostgreSQL + Vector DB]
                                ↓
                        [Future: RAG Service]
                                ↓
                        [Future: API Gateway]
                                ↓
                        [Future: React Frontend]
```

## 🎯 Next Phase (Day 2 MVP)

1. **PostgreSQL Setup**: Create schema for structured storage
2. **Vector Database**: Implement FAISS for embeddings
3. **RAG Service**: Build FastAPI service with LangChain
4. **Embeddings**: Generate from scraped content
5. **Query Pipeline**: Implement semantic search

## 📝 Key Files

- `services/scraper/scrapers/bd_law_crawler.py` - Main crawler logic
- `services/scraper/web_crawler_app.py` - Web UI for manual crawling
- `docker-compose.yml` - Service orchestration
- `start_services.sh` - Startup automation
- `.env` - Configuration (copy from `.env.example`)

## 🧪 Testing

All services have been tested and are working:
- ✅ Scraper imports successfully
- ✅ Web UI starts (requires Redis)
- ✅ Docker configuration valid
- ✅ Scheduler created and functional

## 📚 Resources

- [Architecture Details](ARCHITECTURE.md)
- [MVP Implementation Plan](docs/mvp_implementation_plan.md)
- [System Design](docs/system_design_document.md)
- [Firecrawl API](https://docs.firecrawl.dev/)