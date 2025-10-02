"""
Question-Answer Controller
API endpoints for question answering and chat
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from services.rag_pipeline import RAGPipeline
from services.llm_service import LLMProvider
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize RAG pipeline (singleton)
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline instance"""
    global _rag_pipeline
    if _rag_pipeline is None:
        try:
            # Determine which LLM provider to use
            provider = LLMProvider.GEMINI
            if settings.GEMINI_API_KEY:
                provider = LLMProvider.GEMINI
            elif settings.OPENAI_API_KEY:
                provider = LLMProvider.OPENAI
            else:
                raise ValueError("No LLM API key configured")

            _rag_pipeline = RAGPipeline(llm_provider=provider)
            logger.info(f"RAG Pipeline initialized with provider: {provider.value}")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            raise

    return _rag_pipeline


# Request/Response Models

class AnswerRequest(BaseModel):
    """Request model for question answering"""
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    language: str = Field(default="en", description="Response language (en/bn)")
    top_k: Optional[int] = Field(default=None, ge=1, le=10, description="Number of context documents")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata filters")
    include_sources: bool = Field(default=True, description="Include source documents")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the penalties for theft under Bangladesh law?",
                "language": "en",
                "top_k": 5,
                "filters": {
                    "category": "criminal",
                    "year_min": 1980
                },
                "include_sources": True
            }
        }


class Source(BaseModel):
    """Source document information"""
    source_number: int
    title: str
    act_number: Optional[int]
    section: Optional[str]
    year: Optional[int]
    category: Optional[str]
    relevance_score: float
    excerpt: str


class AnswerResponse(BaseModel):
    """Response model for question answering"""
    question: str
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: List[Source]
    metadata: Dict[str, Any]
    timestamp: datetime


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="Message content")


class ChatRequest(BaseModel):
    """Request model for conversational chat"""
    messages: List[ChatMessage] = Field(..., min_items=1, description="Conversation history")
    language: str = Field(default="en", description="Response language")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "user", "content": "What is theft?"},
                    {"role": "assistant", "content": "Theft is defined in Section 378..."},
                    {"role": "user", "content": "What are the penalties?"}
                ],
                "language": "en"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat"""
    question: str
    answer: str
    confidence: float
    sources: List[Source]
    metadata: Dict[str, Any]
    timestamp: datetime


# API Endpoints

@router.post("/answer", response_model=AnswerResponse, status_code=status.HTTP_200_OK)
async def answer_question(request: AnswerRequest):
    """
    Answer a legal question using RAG

    This endpoint retrieves relevant legal documents and generates
    an answer using an LLM (Gemini or OpenAI).

    Args:
        request: Question and parameters

    Returns:
        Answer with sources and metadata

    Raises:
        HTTPException: If question answering fails
    """
    try:
        logger.info(f"Answering question: {request.question[:100]}...")

        # Get RAG pipeline
        pipeline = get_rag_pipeline()

        # Answer the question
        response = pipeline.answer_question(
            question=request.question,
            language=request.language,
            top_k=request.top_k,
            filters=request.filters,
            include_sources=request.include_sources
        )

        # Convert to response model
        sources = [Source(**source) for source in response.get("sources", [])]

        return AnswerResponse(
            question=response["question"],
            answer=response["answer"],
            confidence=response["confidence"],
            sources=sources,
            metadata=response["metadata"],
            timestamp=response["timestamp"]
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to answer question. Please try again."
        )


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest):
    """
    Conversational interface with message history

    This endpoint supports multi-turn conversations by maintaining
    context from previous messages.

    Args:
        request: Conversation messages

    Returns:
        Response with answer and sources

    Raises:
        HTTPException: If chat fails
    """
    try:
        logger.info(f"Chat request with {len(request.messages)} messages")

        # Validate messages
        if not request.messages:
            raise ValueError("At least one message is required")

        # Get RAG pipeline
        pipeline = get_rag_pipeline()

        # Convert to dict format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        # Process chat
        response = pipeline.chat(
            messages=messages,
            language=request.language
        )

        # Convert to response model
        sources = [Source(**source) for source in response.get("sources", [])]

        return ChatResponse(
            question=response["question"],
            answer=response["answer"],
            confidence=response["confidence"],
            sources=sources,
            metadata=response["metadata"],
            timestamp=response["timestamp"]
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat. Please try again."
        )


@router.get("/pipeline/info", status_code=status.HTTP_200_OK)
async def get_pipeline_info():
    """
    Get information about the RAG pipeline configuration

    Returns:
        Pipeline configuration and statistics
    """
    try:
        pipeline = get_rag_pipeline()
        info = pipeline.get_pipeline_info()

        return {
            "status": "active",
            "pipeline": info,
            "timestamp": datetime.now()
        }

    except Exception as e:
        logger.error(f"Error getting pipeline info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pipeline information"
        )


# Health check for Q&A subsystem
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check for Q&A subsystem

    Returns:
        Health status
    """
    try:
        # Try to get pipeline (will initialize if needed)
        pipeline = get_rag_pipeline()

        return {
            "status": "healthy",
            "subsystem": "question-answering",
            "llm_provider": pipeline.llm_service.provider.value,
            "llm_model": pipeline.llm_service.model,
            "timestamp": datetime.now()
        }

    except Exception as e:
        logger.error(f"Q&A health check failed: {e}")
        return {
            "status": "unhealthy",
            "subsystem": "question-answering",
            "error": str(e),
            "timestamp": datetime.now()
        }


# Additional utility endpoints

class SuggestedQuestion(BaseModel):
    """Suggested question model"""
    question: str
    category: Optional[str]


@router.get("/suggestions", response_model=List[SuggestedQuestion])
async def get_question_suggestions(
    category: Optional[str] = None,
    limit: int = 5
):
    """
    Get suggested questions

    Args:
        category: Optional category filter
        limit: Maximum number of suggestions

    Returns:
        List of suggested questions
    """
    # Predefined suggestions by category
    suggestions = {
        "criminal": [
            "What are the penalties for theft under Bangladesh law?",
            "What constitutes murder according to the Penal Code?",
            "What are the punishments for robbery?",
            "How is assault defined in Bangladesh law?",
            "What is the definition of criminal breach of trust?"
        ],
        "constitutional": [
            "What are the fundamental rights in the Constitution?",
            "What does Article 27 say about equality?",
            "What are the duties of citizens?",
            "How can the Constitution be amended?",
            "What is the structure of the government?"
        ],
        "property": [
            "What are the laws regarding property ownership?",
            "How is property transferred in Bangladesh?",
            "What are the rights of tenants?",
            "What is the law on inheritance?",
            "How are property disputes resolved?"
        ],
        "family": [
            "What are the laws regarding marriage?",
            "What are the grounds for divorce?",
            "What are the rights regarding child custody?",
            "What is the law on maintenance?",
            "How is guardianship determined?"
        ],
        "contract": [
            "What makes a contract valid?",
            "What are the remedies for breach of contract?",
            "When can a contract be voided?",
            "What is consideration in contract law?",
            "What are the requirements for contract formation?"
        ]
    }

    # Get suggestions
    if category and category in suggestions:
        result = suggestions[category][:limit]
    else:
        # Mix from all categories
        result = []
        for cat_questions in suggestions.values():
            result.extend(cat_questions[:2])
            if len(result) >= limit:
                break
        result = result[:limit]

    return [
        SuggestedQuestion(
            question=q,
            category=cat if category else None
        )
        for cat, questions in ([(category, suggestions.get(category, []))] if category else suggestions.items())
        for q in questions[:limit] if not category or cat == category
    ][:limit]


class FeedbackRequest(BaseModel):
    """Feedback request model"""
    question: str = Field(..., description="Original question")
    answer_id: Optional[str] = Field(None, description="Answer ID if available")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    feedback: Optional[str] = Field(None, description="Optional feedback text")


@router.post("/feedback", status_code=status.HTTP_200_OK)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback for an answer

    Args:
        request: Feedback information

    Returns:
        Confirmation
    """
    # TODO: Store feedback in database
    logger.info(
        f"Feedback received - Question: {request.question[:50]}..., "
        f"Rating: {request.rating}, Feedback: {request.feedback[:50] if request.feedback else 'None'}"
    )

    return {
        "status": "received",
        "message": "Thank you for your feedback!",
        "timestamp": datetime.now()
    }
