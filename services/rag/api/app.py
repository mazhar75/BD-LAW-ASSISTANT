"""
FastAPI Application for RAG Service
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Optional

from .routes import health, search, query, admin
from .config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    """
    # Startup
    logger.info("Starting RAG service...")
    # Initialize resources here (database, vector store, etc.)

    yield

    # Shutdown
    logger.info("Shutting down RAG service...")
    # Clean up resources here


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """
    Create and configure FastAPI application

    Args:
        settings: Optional settings object

    Returns:
        FastAPI application instance
    """
    if settings is None:
        settings = Settings()

    # Create FastAPI instance
    app = FastAPI(
        title="BD Law Assistant RAG Service",
        description="Retrieval-Augmented Generation service for Bangladesh legal documents",
        version="1.0.0",
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])

    # Try to use FAISS-enabled query router, fall back to mock if not available
    try:
        from .routes import query_with_faiss
        app.include_router(query_with_faiss.router, prefix="/api/v1/query", tags=["Query"])
        logger.info("Using FAISS-enabled query router")
    except ImportError:
        app.include_router(query.router, prefix="/api/v1/query", tags=["Query"])
        logger.warning("Using mock query router (FAISS not available)")

    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

    # Store settings in app state
    app.state.settings = settings

    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint"""
        return {
            "service": "BD Law Assistant RAG Service",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "search": "/api/v1/search",
                "query": "/api/v1/query",
                "admin": "/api/v1/admin"
            }
        }

    return app