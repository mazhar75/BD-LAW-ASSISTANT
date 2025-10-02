"""
Main entry point for RAG service
"""
import uvicorn
from api import create_app
from api.config import settings

# Create FastAPI app
app = create_app(settings)

if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )