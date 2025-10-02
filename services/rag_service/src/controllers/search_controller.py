"""
Search Controller
Handles semantic search endpoints
"""
from fastapi import APIRouter, HTTPException, Request, status
from typing import List
import logging

from models.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search",
    description="Perform semantic search on legal documents with optional filters"
)
async def search(request: SearchRequest, app_request: Request) -> SearchResponse:
    """
    Semantic search endpoint

    Args:
        request: Search request with query and filters
        app_request: FastAPI request object

    Returns:
        Search response with results and metadata
    """
    try:
        # Get RAG service from app state
        rag_service = app_request.app.state.rag_service

        # Perform search
        response = rag_service.search_from_request(request)

        logger.info(
            f"Search completed: query='{request.query}', "
            f"results={response.total_results}, "
            f"time={response.search_time_ms:.2f}ms"
        )

        return response

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get(
    "/search/suggest",
    response_model=List[str],
    summary="Search suggestions",
    description="Get search suggestions based on query prefix (placeholder)"
)
async def search_suggest(q: str, limit: int = 5) -> List[str]:
    """
    Search suggestion endpoint (placeholder for future implementation)

    Args:
        q: Query prefix
        limit: Maximum number of suggestions

    Returns:
        List of search suggestions
    """
    # TODO: Implement actual suggestion logic
    # For now, return empty list
    return []


@router.post(
    "/search/batch",
    response_model=List[SearchResponse],
    summary="Batch semantic search",
    description="Perform multiple searches in a single request"
)
async def batch_search(
    requests: List[SearchRequest],
    app_request: Request
) -> List[SearchResponse]:
    """
    Batch search endpoint

    Args:
        requests: List of search requests
        app_request: FastAPI request object

    Returns:
        List of search responses
    """
    try:
        # Get RAG service from app state
        rag_service = app_request.app.state.rag_service

        # Perform searches
        responses = []
        for req in requests:
            response = rag_service.search_from_request(req)
            responses.append(response)

        logger.info(f"Batch search completed: {len(requests)} queries")

        return responses

    except Exception as e:
        logger.error(f"Batch search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch search failed: {str(e)}"
        )
