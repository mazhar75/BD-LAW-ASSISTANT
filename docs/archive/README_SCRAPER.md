# BD Law Assistant - Scraping System

## Overview
A scalable, production-ready web scraping system for Bangladesh legal documents using Firecrawl API, Redis queue, and intelligent storage.

## Features
- ✅ **Scalable Architecture**: Redis-based queue for distributed processing
- ✅ **Smart Crawling**: Firecrawl API with retry logic and rate limiting
- ✅ **Content Validation**: Automatic detection of act types, languages, and quality
- ✅ **Efficient Storage**: Compressed storage with deduplication
- ✅ **Bengali Support**: Full support for Bengali legal documents
- ✅ **Monitoring**: Comprehensive logging and metrics tracking

## Quick Start

### Prerequisites
- Python 3.10+
- Redis (or Docker)
- Firecrawl API Key (get from https://firecrawl.dev)

### Installation

1. **Clone and setup environment:**
```bash
cd bd-law-assistant
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your Firecrawl API key
```

3. **Start Redis (if not installed):**
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### Running the Scraper

#### Test Mode (Crawl 5 acts)
```bash
python scrapers/bd_law_crawler.py --test
```

#### Crawl Specific Acts
```bash
python scrapers/bd_law_crawler.py --mode acts --acts 1 2 3 4 5
```

#### Crawl All Volumes
```bash
python scrapers/bd_law_crawler.py --mode volumes
```

#### Full Site Crawl
```bash
python scrapers/bd_law_crawler.py --mode full
```

#### Run as Worker (Process Queue)
```bash
python scrapers/bd_law_crawler.py --mode worker
```

### Docker Deployment

Start all services:
```bash
docker-compose up -d
```

Check logs:
```bash
docker-compose logs -f scraper
```

Stop services:
```bash
docker-compose down
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Firecrawl API  │────>│  Redis Queue    │────>│  File Storage   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  URL Discovery  │     │  Task Processing│     │  Validation     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Project Structure

```
scrapers/
├── core/
│   ├── firecrawl_client.py    # Firecrawl API client
│   └── queue_manager.py        # Redis queue management
├── validators/
│   └── content_validator.py    # Content validation
├── storage/
│   └── file_storage.py        # Document storage
├── config/
│   └── settings.py            # Configuration management
├── utils/
│   └── logger.py              # Logging system
└── bd_law_crawler.py          # Main crawler

data/
├── raw/                       # Raw scraped content
│   ├── volumes/              # Volume pages
│   ├── acts/                 # Act documents
│   └── bengali/              # Bengali content
├── processed/                # Processed data
└── logs/                     # Application logs
```

## Configuration

Key settings in `.env`:

```env
# Firecrawl
FIRECRAWL_API_KEY=your_key_here

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Crawler Settings
CRAWLER_BATCH_SIZE=50          # URLs per batch
CRAWLER_MAX_DEPTH=4           # Crawl depth
CRAWLER_RATE_LIMIT=2          # Seconds between requests
CRAWLER_MAX_RETRIES=3         # Retry attempts

# Storage
DATA_DIR=./data
```

## Monitoring

### Check Queue Status
```python
from scrapers.core.queue_manager import RedisQueueManager
queue = RedisQueueManager()
print(queue.get_queue_status())
```

### View Logs
```bash
tail -f data/logs/*.log
```

### Storage Statistics
```python
from scrapers.storage.file_storage import DocumentStorage
storage = DocumentStorage()
print(storage.get_storage_stats())
```

## Data Output

### File Naming Convention
- Acts: `act_123.html`, `act_123.md`
- Volumes: `volume_1.html`, `volume_1.md`
- Metadata: `act_123.meta.json`

### Metadata Format
```json
{
  "url": "http://bdlaws.minlaw.gov.bd/act-123.html",
  "crawled_at": "2024-01-01T10:00:00",
  "content_hash": "sha256_hash",
  "content_type": "act",
  "language": "bengali",
  "validation": {
    "act_title": "Act No. 123 of 2020",
    "section_count": 45,
    "chapter_count": 5
  }
}
```

## Troubleshooting

### Common Issues

1. **Rate Limiting**
   - Increase `CRAWLER_RATE_LIMIT` in `.env`
   - Reduce `CRAWLER_BATCH_SIZE`

2. **Memory Issues**
   - Use compression: Files are automatically compressed
   - Clean old files: `storage.cleanup_old_files(days=30)`

3. **Failed Tasks**
   - Reprocess: `queue.reprocess_failed()`
   - Check logs: `tail -f data/logs/*.log`

## Performance

- **Crawl Speed**: 50-100 URLs/minute (with rate limiting)
- **Storage**: ~1-5 KB per document (compressed)
- **Queue Capacity**: 100,000+ URLs
- **Deduplication**: Automatic via content hash

## Next Steps

After scraping is complete:
1. Process documents with Go service
2. Generate embeddings for vector search
3. Build FAISS index
4. Integrate with RAG pipeline

## Support

For issues or questions:
- Check logs in `data/logs/`
- Review validation results in metadata files
- Ensure Firecrawl API key is valid
- Verify Redis is running

---

**Version**: 1.0.0
**License**: MIT
**Author**: BD Law Assistant Team