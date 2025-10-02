# BD Law Scraper Service

A scalable web scraping service for Bangladesh legal documents using Firecrawl API. Features bilingual support (English & Bengali), Redis-based task queue, and comprehensive data validation.

## 📋 Overview

The BD Law Scraper Service automates the collection of legal documents from the Bangladesh Ministry of Law website. It uses the Firecrawl API for robust web scraping, Redis for task queuing, and includes a Flask-based web UI for monitoring and control.

### Key Capabilities

- **Bilingual Scraping**: English and Bengali content support
- **Firecrawl Integration**: Reliable scraping with retry logic  
- **Task Queue**: Redis-based distributed task management
- **Data Validation**: Comprehensive validation for legal documents
- **Web UI**: Flask-based monitoring and control interface
- **Batch Processing**: Efficient bulk scraping operations

## 🏗️ Architecture

### Component Details

#### 1. **Firecrawl Client**
- **API**: firecrawl-py (v0.0.16)
- **Timeout**: 600 seconds
- **Retries**: Up to 3 attempts
- **Features**: JSON extraction, markdown conversion

#### 2. **Task Queue (Redis)**
- **Host**: Configurable (default: localhost:6380)
- **Priorities**: HIGH, MEDIUM, LOW
- **Features**: Priority-based dequeuing, task persistence

#### 3. **Content Validator**
- **Schema**: Legal document structure validation
- **Checks**: Metadata completeness, content quality
- **Languages**: English & Bengali support

## ✨ Features

### Scraping Capabilities
- ✅ **Bilingual Support**: English & Bengali content
- ✅ **Volume Discovery**: Automatic detection of law volumes
- ✅ **Act Extraction**: Individual act scraping
- ✅ **Batch Processing**: Bulk scraping with progress tracking
- ✅ **Error Handling**: Retry logic and failure recovery

### Web UI Features
- ✅ **Monitoring Dashboard**: Real-time progress visualization
- ✅ **Manual Control**: Start/stop/pause operations
- ✅ **Range Selection**: Specify act number ranges
- ✅ **Language Toggle**: Switch between EN/BN
- ✅ **Statistics**: Success/failure metrics

## 🛠️ Tech Stack

- **Flask**: Web framework for UI
- **Firecrawl**: API-based web scraping
- **Redis**: Task queue and caching
- **PostgreSQL**: Metadata storage
- **Beautiful Soup**: HTML parsing
- **Pydantic**: Data validation

## 📦 Installation

\`\`\`bash
# Clone repository
git clone <repository-url>
cd services/scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start Redis
redis-server --port 6380

# Run web UI
python web_crawler_app.py
\`\`\`

## ⚙️ Configuration

Create a \`.env\` file:

\`\`\`env
# Firecrawl API
FIRECRAWL_API_KEY=your_api_key_here
FIRECRAWL_BASE_URL=https://api.firecrawl.dev

# Redis
REDIS_HOST=localhost
REDIS_PORT=6380

# Database
DB_HOST=localhost
DB_NAME=bdlaw
DB_USER=postgres
DB_PASSWORD=your_password_here

# Crawler
CRAWLER_BATCH_SIZE=50
CRAWLER_RATE_LIMIT=2.0
\`\`\`

## 🚀 Usage

### Web UI
\`\`\`bash
python web_crawler_app.py
\`\`\`
Visit \`http://localhost:5000\`

### Command Line
\`\`\`bash
# Crawl specific range
python -m scrapers.bd_law_crawler crawl --start 1 --end 100 --language en
\`\`\`

## 📁 Project Structure

\`\`\`
services/scraper/
├── web_crawler_app.py          # Flask web UI
├── scrapers/
│   ├── bd_law_crawler.py       # Main crawler
│   ├── config/settings.py      # Configuration
│   ├── core/                   # Core components
│   ├── storage/                # Storage handlers
│   └── validators/             # Validation logic
├── templates/                  # Web UI templates
├── data/                       # Data directory (git-ignored)
├── .env                        # Config (git-ignored)
├── .gitignore                  # Git ignore rules
└── requirements.txt            # Dependencies
\`\`\`

## 🔒 Security

- API keys stored in \`.env\` (not in code)
- Input validation with Pydantic
- Environment-based configuration
- No secrets committed to git

---

**Built with ❤️ for Bangladesh legal data accessibility**
