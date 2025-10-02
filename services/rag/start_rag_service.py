"""
Startup script for RAG service with proper configuration
"""
import os
import sys
import uvicorn

# Set environment variables
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "bdlaw"
os.environ["DB_USER"] = "postgres"
os.environ["DB_PASSWORD"] = "nihad1086"
os.environ["GEMINI_API_KEY"] = "AIzaSyAgv-iDh_yBSRvSEWI8L25zNHgxk40vISM"
os.environ["DEBUG"] = "True"
os.environ["LOG_LEVEL"] = "INFO"

# Import the app after setting environment variables
from main import app

if __name__ == "__main__":
    print("Starting BD Law RAG Service...")
    print("Database: postgresql://postgres:***@localhost:5432/bdlaw")
    print("Server: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )