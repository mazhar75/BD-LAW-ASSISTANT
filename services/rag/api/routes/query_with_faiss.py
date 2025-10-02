"""
Query endpoints with FAISS integration for Bangladesh Law Assistant RAG API
Replaces mock data with actual document retrieval from FAISS index
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
import time
import uuid
from datetime import datetime
import logging
import os
import sys
import pickle
import numpy as np
from pathlib import Path
import gzip
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import database chunk retriever
try:
    from database.chunk_retriever import get_chunk_by_faiss_index, get_chunks_by_faiss_indices
    CHUNK_RETRIEVAL_AVAILABLE = True
except ImportError:
    CHUNK_RETRIEVAL_AVAILABLE = False
    print("Warning: Chunk retrieval not available")

# Import query processor
try:
    from query_processor import QueryProcessor
    query_processor = QueryProcessor()
    QUERY_PROCESSOR_AVAILABLE = True
except ImportError:
    QUERY_PROCESSOR_AVAILABLE = False
    query_processor = None
    print("Warning: Query processor not available")

# Import FAISS components
try:
    from embeddings.vector_store import VectorStore
    from embeddings.embedding_generator import EmbeddingGenerator
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS components not available")

# Import schemas
from ..schemas import (
    SearchRequest, SearchResponse, SearchResult, DocumentMetadata,
    QuestionRequest, QuestionResponse, SourceDocument,
    SimilarLawsRequest, SimilarLawsResponse, SimilarLaw,
    FeedbackRequest, FeedbackResponse
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["Query"])

# Session store for conversation history
session_store = {}

# FAISS components (initialized on startup)
vector_store = None
embedding_gen = None
id_mappings = None
chunk_metadata = {}


def initialize_faiss():
    """Initialize FAISS components and load the index"""
    global vector_store, embedding_gen, id_mappings, chunk_metadata

    if not FAISS_AVAILABLE:
        logger.warning("FAISS not available - using mock data")
        return False

    try:
        # Initialize embedding generator
        embedding_gen = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        logger.info("Initialized embedding generator")

        # Initialize vector store
        vector_store = VectorStore(
            dimension=embedding_gen.dimension,
            index_type="Flat",
            metric="cosine"
        )

        # Load the existing index
        index_path = Path("../../data/processed/faiss_index.bin")
        if not index_path.exists():
            # Try alternative path
            index_path = Path("data/processed/faiss_index.bin")

        if index_path.exists():
            vector_store.load(str(index_path))
            stats = vector_store.get_stats()
            logger.info(f"Loaded FAISS index with {stats['total_vectors']} vectors")

            # Load ID mappings
            mappings_path = index_path.parent / "id_mappings.pkl"
            if mappings_path.exists():
                with open(mappings_path, 'rb') as f:
                    id_mappings = pickle.load(f)
                logger.info(f"Loaded ID mappings with {len(id_mappings.get('index_to_chunk_id', {}))} entries")

            # Load chunk metadata if available
            chunks_dir = index_path.parent / "chunks"
            if chunks_dir.exists():
                for chunk_file in chunks_dir.glob("*.json.gz"):
                    try:
                        with gzip.open(chunk_file, 'rt') as f:
                            chunk_data = json.load(f)
                            chunk_id = chunk_data.get('chunk_id')
                            if chunk_id:
                                chunk_metadata[chunk_id] = chunk_data
                    except Exception as e:
                        logger.error(f"Error loading chunk {chunk_file}: {e}")
                logger.info(f"Loaded {len(chunk_metadata)} chunk metadata entries")

            return True
        else:
            logger.warning(f"FAISS index not found at {index_path}")
            return False

    except Exception as e:
        logger.error(f"Failed to initialize FAISS: {e}")
        return False


# Initialize FAISS on module load
faiss_initialized = initialize_faiss()


def search_with_faiss(query: str, top_k: int = 5, min_score: float = 0.3) -> List[Dict]:
    """Search for relevant documents using FAISS with enhanced filtering"""
    if not faiss_initialized or not vector_store or not embedding_gen:
        return []

    try:
        # Generate embedding for the query
        query_embedding = embedding_gen.generate_query_embedding(query)

        # Search in FAISS - get more results initially for re-ranking
        initial_k = min(top_k * 3, 15)  # Get 3x results for filtering
        search_results = vector_store.search(
            query_vector=query_embedding,
            k=initial_k,
            threshold=0.15  # Lower threshold initially, filter later
        )

        # Format results
        formatted_results = []
        for idx, score, metadata in search_results:
            # Get additional metadata if available
            result = {
                'index': idx,
                'score': float(score)
            }

            # Retrieve chunk content from database
            if CHUNK_RETRIEVAL_AVAILABLE:
                chunk_data = get_chunk_by_faiss_index(idx)
                if chunk_data:
                    result.update({
                        'content': chunk_data.get('chunk_text', ''),
                        'chunk_id': str(chunk_data.get('db_id', '')),  # Convert to string
                        'title': chunk_data.get('section_title', ''),
                        'law_id': chunk_data.get('law_id'),
                        'language': chunk_data.get('language', 'en'),
                        'category': 'legal'
                    })
                    logger.info(f"Retrieved chunk {idx} from database with {len(chunk_data.get('chunk_text', ''))} chars")
            else:
                # Fallback to metadata from vector store or chunk files
                chunk_id = None
                if id_mappings and 'index_to_chunk_id' in id_mappings:
                    chunk_id = id_mappings['index_to_chunk_id'].get(idx)

                result['chunk_id'] = chunk_id

                # Add chunk content from files if available
                if chunk_id and chunk_id in chunk_metadata:
                    chunk_data = chunk_metadata[chunk_id]
                    result.update({
                        'content': chunk_data.get('content', ''),
                        'source': chunk_data.get('source', ''),
                        'title': chunk_data.get('title', ''),
                        'year': chunk_data.get('year', ''),
                        'category': chunk_data.get('category', 'general')
                    })
                elif metadata:
                    # Use metadata from vector store
                    result.update(metadata)

            formatted_results.append(result)

        # Re-rank and filter results
        if formatted_results:
            # Filter by minimum score
            filtered_results = [r for r in formatted_results if r.get('score', 0) >= min_score]

            # Sort by score (highest first)
            filtered_results.sort(key=lambda x: x.get('score', 0), reverse=True)

            # Apply keyword boost for exact matches
            if QUERY_PROCESSOR_AVAILABLE and query_processor:
                query_lower = query.lower()
                for result in filtered_results:
                    content_lower = result.get('content', '').lower()
                    title_lower = result.get('title', '').lower()

                    # Boost score for exact phrase matches
                    if query_lower in content_lower or query_lower in title_lower:
                        result['score'] *= 1.3

                    # Boost for section number matches
                    sections = query_processor.extract_section_numbers(query)
                    if sections:
                        for section in sections:
                            if f"section {section}" in content_lower:
                                result['score'] *= 1.2

            # Re-sort after boosting
            filtered_results.sort(key=lambda x: x.get('score', 0), reverse=True)

            # Return top-k results
            return filtered_results[:top_k]

        return formatted_results

    except Exception as e:
        logger.error(f"FAISS search error: {e}")
        return []


# ============= Q&A Endpoint with FAISS =============

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest) -> QuestionResponse:
    """
    Ask a question about Bangladesh law and get an AI-generated answer
    Now uses FAISS for document retrieval
    """
    try:
        start_time = time.time()
        query_id = f"q-{uuid.uuid4().hex[:8]}"

        # Get or create session
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:8]}"

        if session_id not in session_store:
            session_store[session_id] = {
                "created_at": datetime.now(),
                "queries": []
            }

        # Process the query for better search results
        original_question = request.question
        search_query = original_question
        query_metadata = {}

        if QUERY_PROCESSOR_AVAILABLE and query_processor:
            processed_query, query_metadata = query_processor.process_query(original_question)

            # Check if it's a greeting
            if query_metadata.get('is_greeting', False):
                # Return a friendly response for greetings
                greeting_response = "Hello! I'm your BD Law Assistant. I can help you with questions about Bangladesh laws, including criminal law, property law, family law, and more. What legal topic would you like to know about?"
                return QuestionResponse(
                    question=original_question,
                    answer=greeting_response,
                    source_documents=None,
                    session_id=session_id,
                    query_id=f"q-{uuid.uuid4().hex[:8]}",
                    confidence_score=1.0,
                    processing_time_ms=10,
                    tokens_used={"input": 5, "output": 30}
                )

            # Use processed query for search
            if processed_query:
                search_query = processed_query
                logger.info(f"Query enhanced: '{original_question}' -> '{search_query}'")

        # Search for relevant documents using FAISS
        search_results = search_with_faiss(search_query, top_k=5)

        # Generate answer based on retrieved documents
        if search_results and search_results[0].get('content'):
            # Combine top results
            context_texts = []
            source_docs = []

            for i, result in enumerate(search_results[:3]):
                if result.get('content'):
                    context_texts.append(result['content'])

                    # Create source document
                    if request.include_sources:
                        source_docs.append(SourceDocument(
                            content_preview=result['content'][:200] + "...",
                            metadata=DocumentMetadata(
                                source=result.get('source', 'unknown'),
                                title=result.get('title', 'Bangladesh Law Document'),
                                year=result.get('year'),
                                category=result.get('category', 'general'),
                                language='en',
                                chunk_id=result.get('chunk_id', f"chunk_{i}")
                            ),
                            relevance_score=result.get('score', 0.0)
                        ))

            # Create answer from retrieved context
            if context_texts:
                context = "\n\n".join(context_texts[:2])  # Use top 2 results
                answer = f"""Based on the Bangladesh legal documents:

{context[:1500]}

This information is retrieved from actual Bangladesh law documents using semantic search. The relevance score is {search_results[0]['score']:.2f}."""

                confidence_score = min(0.95, search_results[0]['score'] + 0.3)  # Boost confidence for real data
            else:
                answer = "I couldn't find specific information about your query in the legal database."
                confidence_score = 0.3
                source_docs = None
        else:
            # No results found - provide general response
            answer = """I couldn't find specific documents matching your query in the Bangladesh legal database.

Please try rephrasing your question or asking about specific acts, laws, or legal topics.
The database contains various Bangladesh acts and legal documents that can help answer questions about:
- Property law
- Criminal law
- Constitutional law
- Contract law
- Family and marriage law
- Labour law
- Tax regulations"""
            confidence_score = 0.2
            source_docs = None

        # Track query
        session_store[session_id]["queries"].append({
            "query_id": query_id,
            "question": request.question,
            "timestamp": datetime.now(),
            "results_found": len(search_results)
        })

        # Calculate token usage (approximate)
        input_tokens = len(request.question.split()) * 2
        output_tokens = len(answer.split()) * 2

        processing_time = (time.time() - start_time) * 1000

        return QuestionResponse(
            question=request.question,
            answer=answer,
            source_documents=source_docs if request.include_sources else None,
            session_id=session_id,
            query_id=query_id,
            confidence_score=confidence_score,
            processing_time_ms=processing_time,
            tokens_used={"input": input_tokens, "output": output_tokens}
        )

    except Exception as e:
        logger.error(f"Q&A error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Search Endpoint with FAISS =============

@router.post("/search", response_model=SearchResponse)
async def search_laws(request: SearchRequest) -> SearchResponse:
    """
    Search Bangladesh laws using FAISS vector similarity search
    """
    try:
        start_time = time.time()

        # Use FAISS search
        search_results = search_with_faiss(request.query, top_k=request.top_k)

        # Format results for response
        formatted_results = []
        for result in search_results:
            if result.get('content'):
                metadata = DocumentMetadata(
                    source=result.get('source', 'unknown'),
                    title=result.get('title', 'Bangladesh Law Document'),
                    year=result.get('year'),
                    category=result.get('category', 'general'),
                    language=request.language,
                    chunk_id=result.get('chunk_id', '')
                )

                search_result = SearchResult(
                    content=result.get('content', ''),
                    metadata=metadata,
                    score=result.get('score', 0.0),
                    highlights=[]  # Could implement keyword highlighting
                )
                formatted_results.append(search_result)

        processing_time = (time.time() - start_time) * 1000

        return SearchResponse(
            query=request.query,
            results=formatted_results,
            total_results=len(formatted_results),
            search_type_used="semantic",  # FAISS uses semantic search
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Similar Laws Endpoint with FAISS =============

@router.post("/similar", response_model=SimilarLawsResponse)
async def find_similar_laws(request: SimilarLawsRequest) -> SimilarLawsResponse:
    """
    Find laws similar to a given text using FAISS
    """
    try:
        start_time = time.time()

        # Use the reference text as query
        search_results = search_with_faiss(request.reference_text, top_k=request.top_k)

        # Format as similar laws
        similar_laws = []
        for result in search_results:
            if result.get('content'):
                metadata = DocumentMetadata(
                    source=result.get('source', 'unknown'),
                    title=result.get('title', 'Bangladesh Law Document'),
                    year=result.get('year'),
                    category=result.get('category', 'general'),
                    language='en',
                    chunk_id=result.get('chunk_id', '')
                )

                similar_law = SimilarLaw(
                    content=result.get('content', ''),
                    metadata=metadata,
                    similarity_score=result.get('score', 0.0),
                    key_similarities=['semantic similarity', 'legal context']
                )
                similar_laws.append(similar_law)

        processing_time = (time.time() - start_time) * 1000

        return SimilarLawsResponse(
            reference_text=request.reference_text[:500],
            similar_laws=similar_laws,
            total_found=len(similar_laws),
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Similar laws error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Feedback Endpoint (same as before) =============

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """Submit feedback about a query response"""
    try:
        feedback_id = f"fb-{uuid.uuid4().hex[:8]}"

        # In production, save to database
        feedback_data = {
            "feedback_id": feedback_id,
            "query_id": request.query_id,
            "feedback_type": request.feedback_type,
            "rating": request.rating,
            "comment": request.comment,
            "correct_answer": request.correct_answer,
            "user_id": request.user_id,
            "timestamp": datetime.now()
        }

        logger.info(f"Feedback received: {feedback_data}")

        return FeedbackResponse(
            feedback_id=feedback_id,
            status="success",
            message="Thank you for your feedback. It has been recorded successfully."
        )

    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Session Management =============

@router.delete("/session/{session_id}")
async def clear_session(session_id: str) -> Dict[str, str]:
    """Clear conversation history for a session"""
    try:
        if session_id in session_store:
            del session_store[session_id]

        return {
            "status": "success",
            "message": f"Session {session_id} cleared successfully"
        }

    except Exception as e:
        logger.error(f"Session clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str) -> Dict[str, Any]:
    """Get conversation history for a session"""
    try:
        if session_id not in session_store:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session_id,
            "session_data": session_store[session_id],
            "faiss_status": "active" if faiss_initialized else "mock_mode"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Status Endpoint =============

@router.get("/status")
async def get_rag_status() -> Dict[str, Any]:
    """Get RAG system status"""
    status = {
        "faiss_initialized": faiss_initialized,
        "vector_store_available": vector_store is not None,
        "embedding_generator_available": embedding_gen is not None,
        "chunks_loaded": len(chunk_metadata),
        "sessions_active": len(session_store)
    }

    if vector_store:
        status.update(vector_store.get_stats())

    return status