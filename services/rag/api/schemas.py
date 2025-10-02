"""
Pydantic models for API request and response schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class LanguageEnum(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    BENGALI = "bn"
    AUTO = "auto"


class SearchType(str, Enum):
    """Types of search"""
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class FeedbackType(str, Enum):
    """Types of feedback"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    CORRECTION = "correction"
    SUGGESTION = "suggestion"


# ============= Request Models =============

class SearchRequest(BaseModel):
    """Request model for search endpoint"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    search_type: SearchType = Field(default=SearchType.HYBRID, description="Type of search")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters (year, category, etc.)")
    language: LanguageEnum = Field(default=LanguageEnum.AUTO, description="Language preference")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "query": "property ownership dispute resolution",
            "top_k": 5,
            "search_type": "hybrid",
            "filters": {"year": 2020, "category": "civil"},
            "language": "en"
        }
    })


class QuestionRequest(BaseModel):
    """Request model for Q&A endpoint"""
    question: str = Field(..., min_length=1, max_length=1000, description="User question")
    use_chat_history: bool = Field(default=False, description="Use conversation history")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation tracking")
    language: LanguageEnum = Field(default=LanguageEnum.AUTO, description="Language preference")
    include_sources: bool = Field(default=True, description="Include source documents")
    max_tokens: int = Field(default=2048, ge=100, le=4096, description="Maximum response tokens")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "question": "What are the penalties for contract breach in Bangladesh?",
            "use_chat_history": False,
            "session_id": "user-123-session-456",
            "language": "en",
            "include_sources": True,
            "max_tokens": 2048
        }
    })


class SimilarLawsRequest(BaseModel):
    """Request model for finding similar laws"""
    reference_text: str = Field(..., min_length=1, max_length=2000, description="Reference text or law section")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of similar laws to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "reference_text": "Section 302 of the Penal Code deals with punishment for murder",
            "top_k": 5,
            "filters": {"category": "criminal"}
        }
    })


class FeedbackRequest(BaseModel):
    """Request model for feedback endpoint"""
    query_id: str = Field(..., description="ID of the query/response being evaluated")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Rating from 1-5")
    comment: Optional[str] = Field(default=None, max_length=1000, description="Additional comments")
    correct_answer: Optional[str] = Field(default=None, description="Correct answer if correction")
    user_id: Optional[str] = Field(default=None, description="User identifier")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "query_id": "q-123-456",
            "feedback_type": "positive",
            "rating": 5,
            "comment": "Very helpful and accurate response",
            "user_id": "user-789"
        }
    })


# ============= Response Models =============

class DocumentMetadata(BaseModel):
    """Metadata for a document"""
    source: str = Field(..., description="Source file or URL")
    title: Optional[str] = Field(default=None, description="Document title")
    year: Optional[int] = Field(default=None, description="Year of publication")
    category: Optional[str] = Field(default=None, description="Document category")
    language: str = Field(default="en", description="Document language")
    chunk_id: Optional[str] = Field(default=None, description="Chunk identifier")


class SearchResult(BaseModel):
    """Individual search result"""
    content: str = Field(..., description="Document content")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    highlights: Optional[List[str]] = Field(default=None, description="Highlighted snippets")


class SearchResponse(BaseModel):
    """Response model for search endpoint"""
    query: str = Field(..., description="Original query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    search_type_used: SearchType = Field(..., description="Search type used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "query": "property ownership",
            "results": [{
                "content": "The Transfer of Property Act 1882...",
                "metadata": {
                    "source": "transfer_property_act_1882.pdf",
                    "title": "Transfer of Property Act",
                    "year": 1882,
                    "category": "civil",
                    "language": "en"
                },
                "score": 0.95,
                "highlights": ["property ownership", "transfer of property"]
            }],
            "total_results": 5,
            "search_type_used": "hybrid",
            "processing_time_ms": 150.5
        }
    })


class SourceDocument(BaseModel):
    """Source document reference"""
    content_preview: str = Field(..., max_length=500, description="Preview of content")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")


class QuestionResponse(BaseModel):
    """Response model for Q&A endpoint"""
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Generated answer")
    source_documents: Optional[List[SourceDocument]] = Field(default=None, description="Source documents")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    query_id: str = Field(..., description="Unique query identifier")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in answer")
    processing_time_ms: float = Field(..., description="Processing time")
    tokens_used: Dict[str, int] = Field(..., description="Token usage statistics")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "question": "What are the penalties for contract breach?",
            "answer": "Under Bangladesh law, penalties for contract breach...",
            "source_documents": [{
                "content_preview": "Section 73 of the Contract Act...",
                "metadata": {
                    "source": "contract_act_1872.pdf",
                    "title": "Contract Act 1872",
                    "year": 1872,
                    "category": "civil",
                    "language": "en"
                },
                "relevance_score": 0.92
            }],
            "session_id": "session-123",
            "query_id": "q-789",
            "confidence_score": 0.85,
            "processing_time_ms": 1250.0,
            "tokens_used": {"input": 450, "output": 350}
        }
    })


class SimilarLaw(BaseModel):
    """Similar law result"""
    content: str = Field(..., description="Law content")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    key_similarities: List[str] = Field(..., description="Key similar concepts")


class SimilarLawsResponse(BaseModel):
    """Response model for similar laws endpoint"""
    reference_text: str = Field(..., max_length=500, description="Reference text preview")
    similar_laws: List[SimilarLaw] = Field(..., description="Similar laws found")
    total_found: int = Field(..., description="Total similar laws found")
    processing_time_ms: float = Field(..., description="Processing time")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "reference_text": "Section 302 of the Penal Code...",
            "similar_laws": [{
                "content": "Section 304 deals with culpable homicide...",
                "metadata": {
                    "source": "penal_code.pdf",
                    "title": "Bangladesh Penal Code",
                    "year": 1860,
                    "category": "criminal",
                    "language": "en"
                },
                "similarity_score": 0.87,
                "key_similarities": ["homicide", "punishment", "criminal intent"]
            }],
            "total_found": 3,
            "processing_time_ms": 200.0
        }
    })


class FeedbackResponse(BaseModel):
    """Response model for feedback endpoint"""
    feedback_id: str = Field(..., description="Unique feedback identifier")
    status: str = Field(..., description="Feedback submission status")
    message: str = Field(..., description="Confirmation message")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "feedback_id": "fb-123-456",
            "status": "success",
            "message": "Thank you for your feedback. It has been recorded successfully."
        }
    })


# ============= Error Models =============

class ErrorDetail(BaseModel):
    """Error detail information"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(default=None, description="Field that caused error")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: ErrorDetail = Field(..., description="Error details")
    request_id: str = Field(..., description="Request identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "error": {
                "code": "INVALID_QUERY",
                "message": "Query must be at least 1 character long",
                "field": "query"
            },
            "request_id": "req-123-456",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    })


# ============= Health Check Models =============

class HealthStatus(BaseModel):
    """Health check status"""
    status: str = Field(..., description="Service status")
    rag_pipeline: bool = Field(..., description="RAG pipeline status")
    vector_store: bool = Field(..., description="Vector store status")
    database: bool = Field(..., description="Database connection status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    version: str = Field(default="1.0.0", description="API version")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "healthy",
            "rag_pipeline": True,
            "vector_store": True,
            "database": True,
            "timestamp": "2024-01-15T10:30:00Z",
            "version": "1.0.0"
        }
    })