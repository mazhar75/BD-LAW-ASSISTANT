# Bangladesh Law RAG Service

## Overview

The RAG (Retrieval-Augmented Generation) service provides intelligent search and question-answering capabilities for Bangladesh law documents. It combines vector similarity search with Google's Gemini AI to provide accurate, context-aware legal information.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                          │
│                    (localhost:3000)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      RAG Service                            │
│                    (localhost:8002)                         │
├─────────────────────────────────────────────────────────────┤
│  Components:                                                │
│  ├── FastAPI Server (api/main.py)                          │
│  ├── RAG Pipeline (rag/rag_pipeline_gemini.py)            │
│  ├── Vector Search (search/vector_search.py)              │
│  ├── Embeddings (embeddings/)                             │
│  └── Database Connection (database/)                       │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
             ▼                           ▼
    ┌────────────────┐         ┌─────────────────┐
    │  PostgreSQL    │         │   FAISS Index   │
    │   Database     │         │  (Vector Store) │
    └────────────────┘         └─────────────────┘
```

## Features

- **Semantic Search**: Find relevant law documents using natural language queries
- **Question Answering**: Get accurate answers to legal questions with source citations
- **Multi-language Support**: Optimized for both English and Bengali text
- **High Performance**: Sub-100ms search latency with efficient vector indexing
- **Source Attribution**: Every answer includes references to specific acts and sections

## Directory Structure

```
services/rag/
├── api/                    # API endpoints
│   └── main.py            # FastAPI server
├── database/              # Database operations
│   ├── connection.py      # PostgreSQL connection pool
│   └── repositories/      # Data access layer
│       ├── law_repository.py
│       └── query_log_repository.py
├── embeddings/            # Text embedding generation
│   ├── embedding_generator.py
│   └── vector_store.py
├── ingestion/             # Data ingestion pipeline
│   ├── document_processor.py
│   └── production_ingest.py
├── rag/                   # RAG pipeline
│   └── rag_pipeline_gemini.py
├── search/                # Search functionality
│   └── vector_search.py
├── utils/                 # Utility functions
│   └── text_utils.py
├── tests/                 # Test suite
│   └── test_complete_rag.py
└── requirements.txt       # Python dependencies
```

## API Endpoints

### 1. Search Endpoint
```http
POST /api/rag/search
Content-Type: application/json

{
  "query": "What is theft under Bangladesh law?",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "What is theft under Bangladesh law?",
  "results": [
    {
      "chunk_id": 12345,
      "text": "Section 378: Theft is defined as...",
      "law_title": "The Penal Code, 1860",
      "act_number": "XLV of 1860",
      "relevance_score": 0.95
    }
  ],
  "total_results": 5,
  "search_time_ms": 85.3
}
```

### 2. Question-Answer Endpoint
```http
POST /api/rag/answer
Content-Type: application/json

{
  "question": "What are the penalties for theft?",
  "context_size": 3
}
```

**Response:**
```json
{
  "question": "What are the penalties for theft?",
  "answer": "Under Section 379 of the Penal Code, simple theft is punishable by imprisonment up to 3 years, or with fine, or both...",
  "sources": [
    {
      "law_title": "The Penal Code, 1860",
      "act_number": "XLV of 1860",
      "section": "379",
      "relevance": 0.96
    }
  ],
  "metadata": {
    "search_time_ms": 95.2,
    "generation_time_ms": 1850.5,
    "total_time_ms": 1945.7,
    "documents_found": 5,
    "model": "gemini-1.5-flash"
  }
}
```

### 3. Health Check
```http
GET /api/rag/health
```

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "database": "connected",
    "vector_index": "loaded",
    "gemini_api": "available"
  },
  "statistics": {
    "total_laws": 300,
    "total_chunks": 29214,
    "index_size": 29214
  }
}
```

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Google Gemini API key

### Setup

1. **Install dependencies:**
```bash
cd services/rag
pip install -r requirements.txt
```

2. **Configure environment variables:**
```bash
# Create .env file in project root
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bdlaw
DB_USER=postgres
DB_PASSWORD=your_password
GEMINI_API_KEY=your_gemini_api_key
```

3. **Initialize database:**
```bash
python database/init_db.py
```

4. **Ingest law documents:**
```bash
python ingestion/production_ingest.py
```

5. **Start the service:**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8002 --reload
```

## Data Pipeline

### 1. Data Sources
- **Raw HTML Files**: `data/raw/acts/*.html.gz`
- **Clean Markdown**: `data/raw/acts/*.md.gz`
- **Processed Chunks**: PostgreSQL database
- **Vector Index**: `data/processed/faiss_index.bin`

### 2. Ingestion Process
```
HTML Files → Clean Markdown → Text Chunks → Embeddings → FAISS Index
                                    ↓
                              PostgreSQL DB
```

### 3. Search Process
```
Query → Embedding → FAISS Search → Top K Results → PostgreSQL Lookup
                                           ↓
                                    Gemini Generation → Answer
```

## Configuration

### RAG Configuration (`rag/rag_pipeline_gemini.py`)
```python
@dataclass
class RAGConfig:
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.1
    max_output_tokens: int = 2048
    top_k: int = 5
    chunk_size: int = 500
    chunk_overlap: int = 100
```

### Search Configuration
```python
# Embedding model
model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
dimension = 384

# Search parameters
similarity_threshold = 0.2
max_results = 10
```

## Testing

Run the complete test suite:
```bash
python tests/test_complete_rag.py
```

Run sample queries:
```bash
python demo_search.py
```

## Performance Metrics

- **Search Latency**: < 100ms
- **Generation Time**: 1-2 seconds
- **Total Response Time**: < 2.5 seconds
- **Throughput**: 50+ requests/second
- **Index Size**: ~112MB for 29,214 vectors

## Integration with API Gateway

The RAG service integrates with the main API gateway through service discovery:

### Gateway Configuration (`api-gateway/src/config/services.js`)
```javascript
module.exports = {
  services: {
    rag: {
      name: 'RAG Service',
      baseUrl: process.env.RAG_SERVICE_URL || 'http://localhost:8002',
      endpoints: {
        search: '/api/rag/search',
        answer: '/api/rag/answer',
        health: '/api/rag/health'
      }
    }
  }
}
```

### Gateway Routes (`api-gateway/src/routes/rag.js`)
```javascript
router.post('/search', async (req, res) => {
  const response = await ragService.search(req.body);
  res.json(response);
});

router.post('/answer', async (req, res) => {
  const response = await ragService.answer(req.body);
  res.json(response);
});
```

## Monitoring

### Logs
- Application logs: `logs/rag_service.log`
- Query logs: Stored in PostgreSQL `query_logs` table

### Metrics
- Request count and latency
- Database query performance
- Vector search accuracy
- Gemini API usage

## Troubleshooting

### Common Issues

1. **"No relevant documents found"**
   - Check if FAISS index is loaded: `ls data/processed/faiss_index.bin`
   - Verify database has data: Check PostgreSQL tables

2. **High latency**
   - Check database indexes
   - Verify FAISS index is in memory
   - Monitor Gemini API response times

3. **Encoding errors**
   - Ensure all text files are UTF-8 encoded
   - Use proper encoding in database connections

## API Usage Examples

### Python Client
```python
import requests

# Search for documents
response = requests.post(
    "http://localhost:8002/api/rag/search",
    json={"query": "theft penalties", "top_k": 5}
)
results = response.json()

# Get answer to question
response = requests.post(
    "http://localhost:8002/api/rag/answer",
    json={"question": "What is criminal breach of trust?"}
)
answer = response.json()
```

### JavaScript Client
```javascript
// Search documents
const searchResponse = await fetch('http://localhost:3000/api/rag/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'theft penalties', top_k: 5 })
});
const results = await searchResponse.json();

// Get answer
const answerResponse = await fetch('http://localhost:3000/api/rag/answer', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question: 'What is criminal breach of trust?' })
});
const answer = await answerResponse.json();
```

## Development

### Adding New Features
1. Create feature branch
2. Update relevant modules
3. Add tests
4. Update API documentation
5. Submit pull request

### Code Style
- Follow PEP 8 for Python code
- Use type hints for function parameters
- Document all public functions
- Keep functions focused and testable

## License

This project is part of the Bangladesh Law Assistant system.

## Contact

For issues and questions, please contact the development team or create an issue in the repository.