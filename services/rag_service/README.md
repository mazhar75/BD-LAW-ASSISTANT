# BD Law Assistant - RAG Service

A production-ready Retrieval-Augmented Generation (RAG) service for Bangladesh legal document search and question answering, powered by ChromaDB vector database and Gemini 2.5 Flash LLM.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Performance](#performance)

## 🌟 Overview

The BD Law Assistant RAG Service provides intelligent legal document search and question-answering capabilities for Bangladesh laws. It combines semantic search using vector embeddings with LLM-powered answer generation to deliver accurate, well-cited legal information.

### Key Capabilities

- **Semantic Search**: Find relevant legal documents using natural language queries
- **Q&A System**: Get intelligent answers with source citations from legal documents
- **Multi-turn Conversations**: Engage in contextual legal discussions
- **Multilingual Support**: Search and answer in both English and Bengali
- **Real-time Processing**: Fast response times with optimized vector search

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│  (Web App, Mobile App, API Clients)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI REST API                         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Search     │  │     Q&A      │  │    Admin     │       │
│  │  Controller  │  │  Controller  │  │  Controller  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                             │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │     RAG      │  │   Embedding  │  │     LLM      │       │
│  │   Service    │  │   Service    │  │   Service    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                │
│                                                             │
│  ┌──────────────────────────┐  ┌────────────────────────┐   │
│  │     ChromaDB Vector      │  │    PostgreSQL DB       │   │
│  │   (29,219 chunks from    │  │   (Legal Documents)    │   │
│  │      300 laws)           │  │                        │   │
│  └──────────────────────────┘  └────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. **Embedding Service**
- **Model**: paraphrase-multilingual-MiniLM-L12-v2
- **Dimension**: 384
- **Languages**: English, Bengali, and 50+ languages
- **Batch Processing**: Up to 32 documents at once

#### 2. **Vector Store (ChromaDB)**
- **Documents**: 29,219 legal document chunks
- **Laws**: 300 Bangladesh laws indexed
- **Distance Metric**: Cosine similarity
- **Index Type**: HNSW (Hierarchical Navigable Small World)

#### 3. **LLM Service**
- **Model**: Gemini 2.5 Flash (Google)
- **Temperature**: 0.1 (factual responses)
- **Max Tokens**: 2,048
- **Features**: Source attribution, confidence scoring

## ✨ Features

### Search Capabilities
- ✅ **Semantic Search**: Natural language queries
- ✅ **Metadata Filtering**: Filter by year, category, law type
- ✅ **Batch Search**: Process multiple queries simultaneously
- ✅ **Relevance Scoring**: Cosine similarity scores for results

### Q&A Capabilities
- ✅ **Answer Generation**: Intelligent responses with LLM
- ✅ **Source Attribution**: Cite specific laws and sections
- ✅ **Multi-turn Chat**: Conversational context awareness
- ✅ **Confidence Scoring**: Quality assessment of answers
- ✅ **Bilingual Support**: English and Bengali responses

## 🛠️ Tech Stack

- **FastAPI**: High-performance web framework
- **ChromaDB**: Vector database for embeddings
- **Sentence Transformers**: Multilingual embeddings
- **Google Gemini**: LLM for answer generation
- **Pydantic**: Data validation and settings

## 📦 Installation

```bash
# Clone repository
git clone <repository-url>
cd services/rag_service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run service
python src/main.py
```

## ⚙️ Configuration

Create a `.env` file:

```env
# LLM Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# PostgreSQL
DB_HOST=localhost
DB_NAME=bdlaw
DB_USER=postgres
DB_PASSWORD=your_password

# ChromaDB
CHROMA_PERSIST_DIR=./data/chroma_data

# Embedding
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
```

## 🚀 Usage

```bash
# Start service
python src/main.py

# API Documentation
http://localhost:8000/docs
```

## 📊 Performance

| Endpoint | Response Time |
|----------|---------------|
| Search   |    ~635ms     |
| Q&A      |    ~4,945ms   |
| Chat     |    ~6,333ms   |

## 🔒 Security

- API keys stored in `.env` (not in code)
- Input validation with Pydantic
- Environment-based configuration
---

**Built with ❤️ for the Bangladesh legal community**
