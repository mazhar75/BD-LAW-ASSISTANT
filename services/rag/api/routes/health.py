"""
Health check endpoints
"""
from fastapi import APIRouter, status
from datetime import datetime
from typing import Dict, Any

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "rag-service"
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """
    Check if service is ready to handle requests
    """
    # TODO: Check database connection
    # TODO: Check vector store loaded
    # TODO: Check embedding model loaded

    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": "ok",
            "vector_store": "ok",
            "embedding_model": "ok"
        }
    }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, bool]:
    """
    Check if service is alive
    """
    return {"alive": True}