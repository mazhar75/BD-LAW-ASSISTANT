"""
Admin Controller
Handles administrative endpoints (health, stats, management)
"""
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from typing import Dict, Any, List
import logging

from models.schemas import (
    HealthResponse,
    StatsResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the RAG service"
)
async def health_check(app_request: Request) -> HealthResponse:
    """
    Health check endpoint

    Args:
        app_request: FastAPI request object

    Returns:
        Health status with component details
    """
    try:
        # Get RAG service from app state
        rag_service = app_request.app.state.rag_service

        # Get health status
        health = rag_service.health_check()

        return HealthResponse(**health)

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            error=str(e)
        )


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get statistics",
    description="Get RAG system statistics including document counts and model info"
)
async def get_stats(app_request: Request) -> StatsResponse:
    """
    Statistics endpoint

    Args:
        app_request: FastAPI request object

    Returns:
        System statistics
    """
    try:
        # Get RAG service from app state
        rag_service = app_request.app.state.rag_service

        # Get statistics
        stats = rag_service.get_stats()

        return StatsResponse(
            vector_store=stats.get('vector_store', {}),
            embedding_model=stats.get('embedding_model', {}),
            status=stats.get('status', 'unknown')
        )

    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


class AddDocumentsRequest(BaseModel):
    """Request model for adding documents"""
    chunk_ids: List[int]
    texts: List[str]
    metadatas: List[Dict[str, Any]]


@router.post(
    "/documents",
    status_code=status.HTTP_201_CREATED,
    summary="Add documents",
    description="Add new documents to the vector store"
)
async def add_documents(
    request_data: AddDocumentsRequest,
    app_request: Request
) -> Dict[str, Any]:
    """
    Add documents endpoint

    Args:
        request_data: Add documents request
        app_request: FastAPI request object

    Returns:
        Success status and count
    """
    try:
        # Validate input lengths
        if len(request_data.chunk_ids) != len(request_data.texts) or len(request_data.chunk_ids) != len(request_data.metadatas):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chunk_ids, texts, and metadatas must have the same length"
            )

        # Get RAG service from app state
        rag_service = app_request.app.state.rag_service

        # Add documents
        success = rag_service.add_documents(request_data.chunk_ids, request_data.texts, request_data.metadatas)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add documents"
            )

        logger.info(f"Added {len(request_data.chunk_ids)} documents")

        return {
            "success": True,
            "count": len(request_data.chunk_ids),
            "message": f"Successfully added {len(request_data.chunk_ids)} documents"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add documents error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add documents: {str(e)}"
        )


@router.get(
    "/documents/{chunk_id}",
    summary="Get document",
    description="Get a specific document by chunk ID"
)
async def get_document(chunk_id: int, app_request: Request) -> Dict[str, Any]:
    """
    Get document endpoint

    Args:
        chunk_id: Chunk ID
        app_request: FastAPI request object

    Returns:
        Document data
    """
    try:
        # Get RAG service from app state
        rag_service = app_request.app.state.rag_service

        # Get document
        document = rag_service.get_document(chunk_id)

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with chunk_id={chunk_id} not found"
            )

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


class DeleteDocumentsRequest(BaseModel):
    """Request model for deleting documents"""
    chunk_ids: List[int]


@router.delete(
    "/documents",
    summary="Delete documents",
    description="Delete documents by chunk IDs"
)
async def delete_documents(
    request_data: DeleteDocumentsRequest,
    app_request: Request
) -> Dict[str, Any]:
    """
    Delete documents endpoint

    Args:
        request_data: Delete documents request
        app_request: FastAPI request object

    Returns:
        Success status and count
    """
    try:
        # Get RAG service from app state
        rag_service = app_request.app.state.rag_service

        # Delete documents
        success = rag_service.delete_documents(request_data.chunk_ids)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete documents"
            )

        logger.info(f"Deleted {len(request_data.chunk_ids)} documents")

        return {
            "success": True,
            "count": len(request_data.chunk_ids),
            "message": f"Successfully deleted {len(request_data.chunk_ids)} documents"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete documents error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete documents: {str(e)}"
        )


@router.post(
    "/reindex",
    summary="Reindex documents",
    description="Trigger reindexing of all documents (placeholder)"
)
async def reindex(app_request: Request) -> Dict[str, Any]:
    """
    Reindex endpoint (placeholder for future implementation)

    Args:
        app_request: FastAPI request object

    Returns:
        Status message
    """
    # TODO: Implement reindexing logic
    logger.warning("Reindex endpoint called but not implemented")

    return {
        "success": True,
        "message": "Reindex functionality not yet implemented"
    }
