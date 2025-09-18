# Automated Data Retrieval & FAISS Vector Storage Pipeline

## Executive Summary
This document outlines the automated pipeline for retrieving Bangladesh legal documents, processing them, and storing vector embeddings in FAISS for efficient semantic search. The system uses Firecrawl for web scraping, Go for concurrent processing, and Python for embedding generation and FAISS management.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Data Sources & Retrieval](#data-sources--retrieval)
3. [Processing Pipeline](#processing-pipeline)
4. [FAISS Vector Storage](#faiss-vector-storage)
5. [Automation Strategy](#automation-strategy)
6. [Implementation Guide](#implementation-guide)
7. [Monitoring & Maintenance](#monitoring--maintenance)

## Architecture Overview

### Pipeline Components
```
┌─────────────────────────────────────────────────────────────────┐
│              AUTOMATED DATA PIPELINE ARCHITECTURE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [1. Data Sources]                                             │
│       ↓                                                        │
│  [2. Firecrawl Scraper] ←→ [Redis Queue]                      │
│       ↓                                                        │
│  [3. Go Processing Service]                                    │
│       ↓                                                        │
│  [4. PostgreSQL Storage]                                       │
│       ↓                                                        │
│  [5. Python Embedding Service]                                 │
│       ↓                                                        │
│  [6. FAISS Index Builder]                                      │
│       ↓                                                        │
│  [7. Vector Storage & Serving]                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Sources & Retrieval

### Primary Sources
```yaml
Main Entry Point:
  URL: http://bdlaws.minlaw.gov.bd/laws-of-bangladesh.html

Crawled Sub-Routes (Automatic):
  - http://bdlaws.minlaw.gov.bd/volume-*.html (All volumes)
  - http://bdlaws.minlaw.gov.bd/act-*.html (All acts)
  - http://bdlaws.minlaw.gov.bd/act-details-*.html (Act details)
  - http://bdlaws.minlaw.gov.bd/pdf_part.php?id=* (PDF sections)
  - http://bdlaws.minlaw.gov.bd/bangla_* (Bengali versions)

Content Types:
  - Acts of Parliament (act-1.html to act-1242.html+)
  - Ordinances
  - Regulations
  - Volumes (volume-1.html to volume-51.html)
  - Amendments & Modifications
  - Bengali translations

Structure:
  - Main Index → Volume Pages → Individual Acts
  - Each Act → Chapters → Sections → Subsections
  - Cross-references and amendments
```

### Firecrawl Configuration

#### 1. Scraper Setup (`/scrapers/firecrawl_config.py`)
```python
import firecrawl
from typing import Dict, List
import redis
import json
from datetime import datetime

class BDLawScraper:
    def __init__(self):
        self.api_key = os.environ['FIRECRAWL_API_KEY']
        self.app = firecrawl.FirecrawlApp(api_key=self.api_key)
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )

    def configure_crawl(self) -> Dict:
        """Configure Firecrawl parameters"""
        return {
            'url': 'http://bdlaws.minlaw.gov.bd/laws-of-bangladesh.html',
            'crawlerOptions': {
                'includes': [
                    '/volume-*.html',     # All volume pages
                    '/act-*.html',        # All act pages
                    '/act-details-*.html', # Detailed act content
                    '/act_sections.php*', # Individual sections
                    '/bangla_*',          # Bengali versions
                    '/print_*'            # Print versions
                ],
                'excludes': [
                    '*.pdf',              # Skip PDF downloads
                    '/download/*',        # Skip download links
                    '/admin/*'            # Skip admin pages
                ],
                'maxDepth': 4,            # Deeper crawl for nested sections
                'limit': 5000,            # Higher limit for complete crawl
                'allowBackwardCrawling': False,
                'allowExternalContentLinks': False
            },
            'pageOptions': {
                'onlyMainContent': True,
                'includeHtml': True,
                'waitFor': 2000,  # Wait for JS rendering
                'screenshot': False
            },
            'timeout': 600000  # 10 minutes timeout
        }

    def crawl_laws(self, batch_size: int = 50):
        """Crawl laws in batches"""
        config = self.configure_crawl()

        # Start crawl job
        crawl_job = self.app.crawl_url(**config)

        # Process in batches
        for i in range(0, len(crawl_job['data']), batch_size):
            batch = crawl_job['data'][i:i+batch_size]

            # Push to Redis queue for processing
            for page in batch:
                self.redis_client.lpush(
                    'crawl_queue',
                    json.dumps({
                        'url': page['url'],
                        'content': page['markdown'],
                        'html': page['html'],
                        'metadata': page['metadata'],
                        'crawled_at': datetime.now().isoformat()
                    })
                )

            # Rate limiting
            time.sleep(2)  # 2 seconds between batches
```

#### 2. Incremental Crawling
```python
class IncrementalCrawler:
    def __init__(self, scraper: BDLawScraper):
        self.scraper = scraper
        self.db = PostgreSQLClient()

    def get_last_crawl_timestamp(self) -> datetime:
        """Get timestamp of last successful crawl"""
        query = "SELECT MAX(crawled_at) FROM crawl_history"
        return self.db.execute(query)[0][0]

    def detect_changes(self) -> List[str]:
        """Detect new or modified pages"""
        last_crawl = self.get_last_crawl_timestamp()

        # Crawl sitemap or index page
        sitemap_data = self.scraper.app.scrape_url(
            url='http://bdlaws.minlaw.gov.bd/sitemap.xml'
        )

        changed_urls = []
        for url in sitemap_data['urls']:
            if url['lastmod'] > last_crawl:
                changed_urls.append(url['loc'])

        return changed_urls

    def incremental_crawl(self):
        """Crawl only new or updated content"""
        changed_urls = self.detect_changes()

        for url in changed_urls:
            page_data = self.scraper.app.scrape_url(url=url)

            # Queue for processing
            self.scraper.redis_client.lpush(
                'crawl_queue',
                json.dumps(page_data)
            )
```

## Processing Pipeline

### Go Processing Service

#### 1. Document Parser (`/go-service/internal/parser/document_parser.go`)
```go
package parser

import (
    "encoding/json"
    "regexp"
    "strings"
    "sync"
)

type LegalDocument struct {
    ID           string            `json:"id"`
    ActName      string            `json:"act_name"`
    ActNumber    string            `json:"act_number"`
    Year         int               `json:"year"`
    Chapters     []Chapter         `json:"chapters"`
    RawContent   string            `json:"raw_content"`
    Metadata     map[string]string `json:"metadata"`
}

type Chapter struct {
    Number   string    `json:"number"`
    Title    string    `json:"title"`
    Sections []Section `json:"sections"`
}

type Section struct {
    Number  string `json:"number"`
    Title   string `json:"title"`
    Content string `json:"content"`
}

type DocumentParser struct {
    workers int
    queue   chan *RawDocument
    results chan *LegalDocument
}

func NewDocumentParser(workers int) *DocumentParser {
    return &DocumentParser{
        workers: workers,
        queue:   make(chan *RawDocument, 100),
        results: make(chan *LegalDocument, 100),
    }
}

func (dp *DocumentParser) ProcessBatch(documents []*RawDocument) []*LegalDocument {
    var wg sync.WaitGroup

    // Start worker goroutines
    for i := 0; i < dp.workers; i++ {
        wg.Add(1)
        go dp.worker(&wg)
    }

    // Queue documents
    go func() {
        for _, doc := range documents {
            dp.queue <- doc
        }
        close(dp.queue)
    }()

    // Collect results
    go func() {
        wg.Wait()
        close(dp.results)
    }()

    var processed []*LegalDocument
    for doc := range dp.results {
        processed = append(processed, doc)
    }

    return processed
}

func (dp *DocumentParser) worker(wg *sync.WaitGroup) {
    defer wg.Done()

    for raw := range dp.queue {
        parsed := dp.parseDocument(raw)
        dp.results <- parsed
    }
}

func (dp *DocumentParser) parseDocument(raw *RawDocument) *LegalDocument {
    doc := &LegalDocument{
        ID:       generateUUID(),
        Metadata: make(map[string]string),
    }

    // Extract act name and number
    actPattern := regexp.MustCompile(`(?i)(.+?)\s+Act[,\s]+(\d{4})`)
    if matches := actPattern.FindStringSubmatch(raw.Content); len(matches) > 0 {
        doc.ActName = strings.TrimSpace(matches[1])
        doc.Year = parseYear(matches[2])
    }

    // Parse chapters and sections
    doc.Chapters = dp.parseChapters(raw.Content)

    // Clean and store raw content
    doc.RawContent = dp.cleanContent(raw.Content)

    return doc
}
```

#### 2. Text Chunking Service (`/go-service/internal/chunker/text_chunker.go`)
```go
package chunker

import (
    "strings"
    "unicode"
)

type ChunkConfig struct {
    ChunkSize    int  // Target chunk size in tokens
    Overlap      int  // Overlap between chunks
    RespectSentences bool // Don't break mid-sentence
}

type Chunk struct {
    ID       string                 `json:"id"`
    DocID    string                 `json:"doc_id"`
    Index    int                    `json:"index"`
    Text     string                 `json:"text"`
    Metadata map[string]interface{} `json:"metadata"`
}

type TextChunker struct {
    config ChunkConfig
}

func NewTextChunker(config ChunkConfig) *TextChunker {
    return &TextChunker{config: config}
}

func (tc *TextChunker) ChunkDocument(doc *LegalDocument) []Chunk {
    var chunks []Chunk

    // Process each section
    for _, chapter := range doc.Chapters {
        for _, section := range chapter.Sections {
            sectionChunks := tc.chunkText(
                section.Content,
                map[string]interface{}{
                    "act_name": doc.ActName,
                    "chapter":  chapter.Number,
                    "section":  section.Number,
                    "year":     doc.Year,
                },
            )

            for i, chunk := range sectionChunks {
                chunks = append(chunks, Chunk{
                    ID:       generateChunkID(doc.ID, len(chunks)),
                    DocID:    doc.ID,
                    Index:    len(chunks),
                    Text:     chunk,
                    Metadata: sectionChunks[i].Metadata,
                })
            }
        }
    }

    return chunks
}

func (tc *TextChunker) chunkText(text string, metadata map[string]interface{}) []Chunk {
    // Tokenize text
    tokens := tc.tokenize(text)

    var chunks []Chunk
    for i := 0; i < len(tokens); i += (tc.config.ChunkSize - tc.config.Overlap) {
        end := min(i+tc.config.ChunkSize, len(tokens))

        chunkTokens := tokens[i:end]
        chunkText := tc.detokenize(chunkTokens)

        // Ensure we don't break sentences
        if tc.config.RespectSentences {
            chunkText = tc.completeSentence(chunkText, text)
        }

        chunks = append(chunks, Chunk{
            Text:     chunkText,
            Metadata: metadata,
        })

        if end >= len(tokens) {
            break
        }
    }

    return chunks
}
```

### PostgreSQL Storage

#### Database Schema
```sql
-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    act_name VARCHAR(500) NOT NULL,
    act_number VARCHAR(100),
    year INTEGER,
    source_url VARCHAR(500),
    raw_content TEXT,
    processed_content JSONB,
    crawled_at TIMESTAMP,
    processed_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'pending',
    INDEX idx_act_name (act_name),
    INDEX idx_year (year),
    INDEX idx_status (status)
);

-- Chunks table
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    chunk_index INTEGER,
    chunk_text TEXT NOT NULL,
    chunk_metadata JSONB,
    embedding_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_document (document_id),
    INDEX idx_embedding (embedding_id)
);

-- Crawl history
CREATE TABLE crawl_history (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500),
    status VARCHAR(50),
    pages_crawled INTEGER,
    documents_processed INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    INDEX idx_status (status),
    INDEX idx_completed (completed_at)
);
```

## FAISS Vector Storage

### Embedding Generation Pipeline

#### 1. Embedding Service (`/rag-service/embeddings/embedding_generator.py`)
```python
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict
import pickle
import os

class EmbeddingGenerator:
    def __init__(self, model_name: str = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'):
        """Initialize multilingual embedding model"""
        self.model = SentenceTransformer(model_name)
        self.dimension = 768  # Model output dimension

    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for text chunks"""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(
                batch,
                normalize_embeddings=True,  # For cosine similarity
                show_progress_bar=True,
                convert_to_numpy=True
            )
            embeddings.append(batch_embeddings)

        return np.vstack(embeddings)
```

#### 2. FAISS Index Builder (`/rag-service/faiss/index_builder.py`)
```python
import faiss
import numpy as np
import pickle
from typing import List, Dict, Tuple
import json

class FAISSIndexBuilder:
    def __init__(self, dimension: int = 768, index_type: str = 'IVF'):
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.metadata = {}  # Store chunk metadata

    def create_index(self, num_vectors: int):
        """Create FAISS index based on data size"""
        if num_vectors < 10000:
            # Use flat index for small datasets
            self.index = faiss.IndexFlatIP(self.dimension)
        else:
            # Use IVF index for larger datasets
            nlist = min(4096, int(np.sqrt(num_vectors)))
            quantizer = faiss.IndexFlatIP(self.dimension)
            self.index = faiss.IndexIVFFlat(
                quantizer,
                self.dimension,
                nlist,
                faiss.METRIC_INNER_PRODUCT
            )

    def build_index(self, embeddings: np.ndarray, chunks: List[Dict]):
        """Build FAISS index from embeddings"""
        num_vectors = len(embeddings)

        # Create appropriate index
        self.create_index(num_vectors)

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)

        # Train index if needed (for IVF)
        if hasattr(self.index, 'train'):
            print(f"Training index with {num_vectors} vectors...")
            self.index.train(embeddings)

        # Add vectors to index
        self.index.add(embeddings)

        # Store metadata
        for i, chunk in enumerate(chunks):
            self.metadata[i] = {
                'chunk_id': chunk['id'],
                'document_id': chunk['document_id'],
                'text': chunk['text'],
                'act_name': chunk.get('act_name'),
                'section': chunk.get('section'),
                'chapter': chunk.get('chapter')
            }

        print(f"Index built with {self.index.ntotal} vectors")

    def save_index(self, path: str):
        """Save index and metadata to disk"""
        # Save FAISS index
        faiss.write_index(self.index, f"{path}/faiss.index")

        # Save metadata
        with open(f"{path}/metadata.pkl", 'wb') as f:
            pickle.dump(self.metadata, f)

        # Save index info
        info = {
            'dimension': self.dimension,
            'index_type': self.index_type,
            'num_vectors': self.index.ntotal,
            'created_at': datetime.now().isoformat()
        }
        with open(f"{path}/index_info.json", 'w') as f:
            json.dump(info, f, indent=2)

    def load_index(self, path: str):
        """Load index and metadata from disk"""
        # Load FAISS index
        self.index = faiss.read_index(f"{path}/faiss.index")

        # Load metadata
        with open(f"{path}/metadata.pkl", 'rb') as f:
            self.metadata = pickle.load(f)

        print(f"Loaded index with {self.index.ntotal} vectors")
```

#### 3. Vector Search Service (`/rag-service/faiss/search_service.py`)
```python
class VectorSearchService:
    def __init__(self, index_path: str):
        self.index_builder = FAISSIndexBuilder()
        self.index_builder.load_index(index_path)
        self.embedding_generator = EmbeddingGenerator()

    def search(self, query: str, k: int = 10, filter_metadata: Dict = None) -> List[Dict]:
        """Search for similar documents"""
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embeddings([query])
        faiss.normalize_L2(query_embedding)

        # Search in index
        distances, indices = self.index_builder.index.search(query_embedding, k * 2)

        # Get results with metadata
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # No more results
                break

            metadata = self.index_builder.metadata[idx]

            # Apply metadata filters if provided
            if filter_metadata:
                skip = False
                for key, value in filter_metadata.items():
                    if metadata.get(key) != value:
                        skip = True
                        break
                if skip:
                    continue

            results.append({
                'score': float(dist),
                'text': metadata['text'],
                'metadata': metadata,
                'rank': i + 1
            })

            if len(results) >= k:
                break

        return results

    def update_index(self, new_chunks: List[Dict]):
        """Add new chunks to existing index"""
        # Generate embeddings for new chunks
        texts = [chunk['text'] for chunk in new_chunks]
        new_embeddings = self.embedding_generator.generate_embeddings(texts)

        # Normalize
        faiss.normalize_L2(new_embeddings)

        # Add to index
        start_id = self.index_builder.index.ntotal
        self.index_builder.index.add(new_embeddings)

        # Update metadata
        for i, chunk in enumerate(new_chunks):
            self.index_builder.metadata[start_id + i] = chunk

        print(f"Added {len(new_chunks)} new vectors to index")
```

## Automation Strategy

### 1. Orchestration Service (`/automation/orchestrator.py`)
```python
import schedule
import time
from celery import Celery
from datetime import datetime
import logging

# Celery configuration
app = Celery('bd_law_pipeline', broker='redis://localhost:6379')

class PipelineOrchestrator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scraper = BDLawScraper()
        self.processor = DocumentProcessor()
        self.embedder = EmbeddingGenerator()
        self.index_builder = FAISSIndexBuilder()

    @app.task
    def full_pipeline_run(self):
        """Complete pipeline execution"""
        try:
            # Step 1: Crawl new data
            self.logger.info("Starting crawl...")
            crawl_job_id = self.scraper.crawl_laws()

            # Step 2: Process documents (Go service)
            self.logger.info("Processing documents...")
            processed_count = self.process_crawled_data(crawl_job_id)

            # Step 3: Generate embeddings
            self.logger.info("Generating embeddings...")
            embedding_count = self.generate_embeddings()

            # Step 4: Update FAISS index
            self.logger.info("Updating FAISS index...")
            self.update_faiss_index()

            # Step 5: Validate and backup
            self.validate_and_backup()

            return {
                'status': 'success',
                'processed': processed_count,
                'embeddings': embedding_count,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            self.send_alert(f"Pipeline failure: {str(e)}")
            raise

    @app.task
    def incremental_update(self):
        """Incremental update for new/modified content"""
        try:
            # Detect changes
            changed_urls = self.detect_changes()

            if not changed_urls:
                self.logger.info("No changes detected")
                return

            # Process only changed content
            for url in changed_urls:
                self.process_single_document(url)

            # Update index
            self.update_faiss_index(incremental=True)

        except Exception as e:
            self.logger.error(f"Incremental update failed: {str(e)}")
            raise
```

### 2. Scheduler Configuration (`/automation/scheduler.py`)
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

class PipelineScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.orchestrator = PipelineOrchestrator()
        self.timezone = pytz.timezone('Asia/Dhaka')

    def setup_schedules(self):
        """Configure automated runs"""

        # Daily incremental updates at 2 AM
        self.scheduler.add_job(
            func=self.orchestrator.incremental_update,
            trigger=CronTrigger(
                hour=2,
                minute=0,
                timezone=self.timezone
            ),
            id='daily_incremental',
            name='Daily Incremental Update',
            misfire_grace_time=3600
        )

        # Weekly full crawl on Sunday at 3 AM
        self.scheduler.add_job(
            func=self.orchestrator.full_pipeline_run,
            trigger=CronTrigger(
                day_of_week='sun',
                hour=3,
                minute=0,
                timezone=self.timezone
            ),
            id='weekly_full_crawl',
            name='Weekly Full Crawl'
        )

        # Monthly index optimization
        self.scheduler.add_job(
            func=self.optimize_faiss_index,
            trigger=CronTrigger(
                day=1,
                hour=4,
                minute=0,
                timezone=self.timezone
            ),
            id='monthly_optimization',
            name='Monthly Index Optimization'
        )

    def optimize_faiss_index(self):
        """Optimize and compact FAISS index"""
        # Load current index
        index_builder = FAISSIndexBuilder()
        index_builder.load_index('/data/faiss')

        # Rebuild with optimization
        if index_builder.index.ntotal > 100000:
            # Convert to more efficient index type for large datasets
            new_index = faiss.index_factory(
                index_builder.dimension,
                "IVF4096,PQ64",
                faiss.METRIC_INNER_PRODUCT
            )

            # Train and add vectors
            vectors = index_builder.get_all_vectors()
            new_index.train(vectors)
            new_index.add(vectors)

            # Save optimized index
            index_builder.index = new_index
            index_builder.save_index('/data/faiss_optimized')
```

### 3. Docker Compose for Automation
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: bdlaw
      POSTGRES_USER: bdlaw
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  celery-worker:
    build: ./automation
    command: celery -A orchestrator worker --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://bdlaw:${DB_PASSWORD}@postgres:5432/bdlaw
    volumes:
      - ./data:/data
      - ./logs:/logs

  celery-beat:
    build: ./automation
    command: celery -A orchestrator beat --loglevel=info
    depends_on:
      - redis
      - postgres
    volumes:
      - ./data:/data

  go-processor:
    build: ./go-service
    ports:
      - "8001:8001"
    depends_on:
      - postgres
      - redis
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://bdlaw:${DB_PASSWORD}@postgres:5432/bdlaw

  embedding-service:
    build: ./rag-service
    ports:
      - "8002:8002"
    depends_on:
      - postgres
    volumes:
      - ./data/faiss:/data/faiss
      - ./models:/models
    environment:
      - DATABASE_URL=postgresql://bdlaw:${DB_PASSWORD}@postgres:5432/bdlaw
      - MODEL_CACHE=/models

volumes:
  redis_data:
  postgres_data:
```

## Implementation Guide

### Step 1: Initial Setup
```bash
# 1. Clone repository
git clone https://github.com/your-org/bd-law-assistant.git
cd bd-law-assistant

# 2. Create directories
mkdir -p data/{scraped,processed,faiss,backups}
mkdir -p logs
mkdir -p models

# 3. Install dependencies
pip install -r requirements.txt
go mod download
npm install

# 4. Set environment variables
cp .env.example .env
# Edit .env with your API keys and configurations

# 5. Initialize database
psql -U postgres -f scripts/init_db.sql

# 6. Download embedding model
python scripts/download_models.py
```

### Step 2: First-Time Data Load
```python
# scripts/initial_load.py
from automation.orchestrator import PipelineOrchestrator

def initial_data_load():
    """Perform initial data load"""
    orchestrator = PipelineOrchestrator()

    # Step 1: Crawl all laws
    print("Starting initial crawl...")
    orchestrator.scraper.crawl_all_laws(
        batch_size=100,
        delay=5  # 5 seconds between batches
    )

    # Step 2: Process all documents
    print("Processing documents...")
    orchestrator.process_all_documents()

    # Step 3: Generate all embeddings
    print("Generating embeddings...")
    orchestrator.generate_all_embeddings(batch_size=1000)

    # Step 4: Build FAISS index
    print("Building FAISS index...")
    orchestrator.build_complete_index()

    print("Initial load complete!")

if __name__ == "__main__":
    initial_data_load()
```

### Step 3: Start Automation Services
```bash
# Start all services
docker-compose up -d

# Start scheduler
python automation/scheduler.py

# Monitor logs
tail -f logs/pipeline.log

# Check pipeline status
curl http://localhost:8000/api/pipeline/status
```

## Monitoring & Maintenance

### 1. Health Checks
```python
# monitoring/health_check.py
class PipelineHealthCheck:
    def __init__(self):
        self.checks = {
            'redis': self.check_redis,
            'postgres': self.check_postgres,
            'faiss': self.check_faiss,
            'crawler': self.check_crawler
        }

    def run_all_checks(self) -> Dict:
        """Run all health checks"""
        results = {}
        for name, check_func in self.checks.items():
            try:
                results[name] = check_func()
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'message': str(e)
                }
        return results

    def check_faiss(self) -> Dict:
        """Check FAISS index health"""
        index_path = '/data/faiss'

        if not os.path.exists(f"{index_path}/faiss.index"):
            return {'status': 'error', 'message': 'Index not found'}

        index_builder = FAISSIndexBuilder()
        index_builder.load_index(index_path)

        return {
            'status': 'healthy',
            'vectors': index_builder.index.ntotal,
            'last_updated': os.path.getmtime(f"{index_path}/faiss.index")
        }
```

### 2. Performance Metrics
```yaml
Metrics to Track:
  Crawling:
    - Pages per minute
    - Success rate
    - Error types

  Processing:
    - Documents per minute
    - Chunk generation rate
    - Go service CPU/Memory

  Embedding:
    - Vectors per second
    - Model inference time
    - GPU utilization

  FAISS:
    - Index size
    - Search latency
    - Memory usage

  Pipeline:
    - End-to-end time
    - Queue lengths
    - Failed jobs
```

### 3. Backup Strategy
```python
# backup/backup_manager.py
class BackupManager:
    def __init__(self):
        self.backup_dir = '/data/backups'

    def backup_faiss_index(self):
        """Backup FAISS index"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.backup_dir}/faiss_{timestamp}"

        # Copy index files
        shutil.copytree('/data/faiss', backup_path)

        # Compress
        shutil.make_archive(backup_path, 'zip', backup_path)

        # Clean old backups (keep last 7)
        self.cleanup_old_backups(keep=7)

    def restore_faiss_index(self, backup_file: str):
        """Restore FAISS index from backup"""
        # Extract backup
        shutil.unpack_archive(backup_file, '/data/faiss_restore')

        # Verify index
        test_builder = FAISSIndexBuilder()
        test_builder.load_index('/data/faiss_restore')

        # Replace current index
        shutil.rmtree('/data/faiss')
        shutil.move('/data/faiss_restore', '/data/faiss')
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Crawling Issues
```python
# Rate limiting errors
Solution: Increase delay between requests
config['crawlerOptions']['delay'] = 5000  # 5 seconds

# Timeout errors
Solution: Increase timeout and implement retry
config['timeout'] = 1200000  # 20 minutes
```

#### 2. Memory Issues with FAISS
```python
# Large index memory usage
Solution: Use memory-mapped index
index = faiss.read_index('/data/faiss.index', faiss.IO_FLAG_MMAP)

# OOM during index building
Solution: Build in batches
for batch in chunks(embeddings, 10000):
    index.add(batch)
```

#### 3. Embedding Generation Bottlenecks
```python
# Slow embedding generation
Solution: Use GPU and batch processing
model = SentenceTransformer(model_name, device='cuda')
embeddings = model.encode(texts, batch_size=64)
```

## Performance Optimization

### 1. Index Optimization
```python
def optimize_index_for_size(index, vectors):
    """Optimize index based on dataset size"""
    n_vectors = len(vectors)

    if n_vectors < 10000:
        # Use flat index for small datasets
        return faiss.IndexFlatIP(dimension)
    elif n_vectors < 100000:
        # Use IVF for medium datasets
        nlist = int(np.sqrt(n_vectors))
        quantizer = faiss.IndexFlatIP(dimension)
        index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
    else:
        # Use PQ for large datasets
        index = faiss.index_factory(
            dimension,
            "IVF4096,PQ64",
            faiss.METRIC_INNER_PRODUCT
        )

    return index
```

### 2. Query Optimization
```python
def optimized_search(query, k=10):
    """Optimized search with caching"""
    # Check cache first
    cache_key = hashlib.md5(query.encode()).hexdigest()
    cached = redis_client.get(f"search:{cache_key}")

    if cached:
        return json.loads(cached)

    # Perform search
    results = vector_search.search(query, k)

    # Cache results
    redis_client.setex(
        f"search:{cache_key}",
        3600,  # 1 hour TTL
        json.dumps(results)
    )

    return results
```

## Conclusion

This automated pipeline provides:
1. **Reliable data retrieval** using Firecrawl with rate limiting and error handling
2. **Efficient processing** with Go's concurrent architecture
3. **Optimized vector storage** using FAISS with appropriate index types
4. **Full automation** with scheduled crawls, incremental updates, and monitoring
5. **Scalability** through batch processing and index optimization

The system can handle millions of documents while maintaining sub-second search performance and automatically staying synchronized with the source website.

---

*Document Version: 1.0*
*Last Updated: 2025-09-17*
*For: BD Law Assistant Data Pipeline*