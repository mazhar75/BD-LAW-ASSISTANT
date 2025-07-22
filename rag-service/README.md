# RAG Microservice

This directory contains the Python Retrieval-Augmented Generation (RAG) microservice for BD Law Assistant.

## Features
- Embedding, retrieval, and generation of legal answers
- Integrates with vector store (FAISS/Pinecone/Weaviate)
- Exposes REST/gRPC API for API Gateway

## Structure
- `app/` - Main FastAPI/Flask application code

## Setup
1. Ensure you have Python 3.9+ and pip installed.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the service:
   ```
   uvicorn app.main:app --reload
   ```
   (or the appropriate entrypoint)

## Configuration
- Edit `.env` or config files for vector store, database, etc.

## Development
- See the main project README for architecture and integration details. 