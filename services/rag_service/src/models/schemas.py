"""
Pydantic schemas for request/response models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# Search Request/Response Models
class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    language: str = Field(default="en", description="Query language (en/bn)")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Similarity threshold")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "query": "fundamental rights in constitution",
                "language": "en",
                "top_k": 5,
                "threshold": 0.7,
                "filters": {"category": "constitutional"}
            }]
        }
    }


class SearchResult(BaseModel):
    """Single search result"""
    chunk_id: int
    act_number: int
    title: str
    content: str
    section: Optional[str] = None
    score: float
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    timestamp: datetime

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "query": "fundamental rights",
                "results": [
                    {
                        "chunk_id": 123,
                        "act_number": 1,
                        "title": "Constitution of Bangladesh",
                        "content": "The Constitution guarantees...",
                        "section": "Article 27",
                        "score": 0.95,
                        "metadata": {"year": 1972}
                    }
                ],
                "total_results": 1,
                "search_time_ms": 45.2,
                "timestamp": "2025-10-01T00:00:00Z"
            }]
        }
    }


# Document Models
class DocumentMetadata(BaseModel):
    """Document metadata model"""
    chunk_id: int
    law_id: int
    act_number: int
    title: str
    section_title: Optional[str] = None
    section_number: Optional[str] = None
    year: Optional[int] = None
    category: Optional[str] = None
    language: str = "en"
    chunk_index: int
    token_count: Optional[int] = None


class Document(BaseModel):
    """Document model for ChromaDB"""
    id: str
    text: str
    metadata: DocumentMetadata


# Stats Models
class StatsResponse(BaseModel):
    """Statistics response model"""
    vector_store: Dict[str, Any]
    embedding_model: Dict[str, Any]
    status: str


# Health Check Models
class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    vector_store: Optional[str] = None
    embedding_service: Optional[str] = None
    total_documents: Optional[int] = None
    error: Optional[str] = None


# Error Models
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
