"""
Main FastAPI Application
Entry point for the RAG Service API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config.settings import settings
from services.rag_service import RAGService
from controllers.search_controller import router as search_router
from controllers.admin_controller import router as admin_router
from controllers.qa_controller import router as qa_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global RAG service instance
rag_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    global rag_service
    logger.info("Starting RAG Service...")

    try:
        rag_service = RAGService()
        app.state.rag_service = rag_service
        logger.info("RAG Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG Service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down RAG Service...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="RAG Service API for Bangladesh legal documents with LLM-powered Q&A",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_router, prefix=settings.API_PREFIX, tags=["Search"])
app.include_router(qa_router, prefix=f"{settings.API_PREFIX}/qa", tags=["Question & Answer"])
app.include_router(admin_router, prefix=f"{settings.API_PREFIX}/admin", tags=["Admin"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "search": f"{settings.API_PREFIX}/search",
            "answer": f"{settings.API_PREFIX}/qa/answer",
            "chat": f"{settings.API_PREFIX}/qa/chat",
            "admin": f"{settings.API_PREFIX}/admin/stats",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
