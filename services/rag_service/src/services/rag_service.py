"""
RAG Service
Combines embedding generation and vector search for semantic retrieval
"""
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from models.chroma_vector_store import ChromaVectorStore
from services.embedding_service import EmbeddingService
from models.schemas import SearchRequest, SearchResponse, SearchResult
from config.settings import settings

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for semantic search and retrieval"""

    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        Initialize RAG service

        Args:
            vector_store: ChromaDB vector store instance
            embedding_service: Embedding service instance
        """
        # Initialize vector store
        if vector_store is None:
            self.vector_store = ChromaVectorStore(
                collection_name=settings.CHROMA_COLLECTION_NAME,
                persist_directory=settings.CHROMA_PERSIST_DIR,
                embedding_model=settings.EMBEDDING_MODEL,
                distance_metric=settings.CHROMA_DISTANCE_METRIC
            )
        else:
            self.vector_store = vector_store

        # Initialize embedding service (not needed for ChromaDB as it has built-in embeddings)
        # But we keep it for flexibility and custom operations
        if embedding_service is None:
            self.embedding_service = EmbeddingService(
                model_name=settings.EMBEDDING_MODEL,
                batch_size=settings.EMBEDDING_BATCH_SIZE,
                device=settings.EMBEDDING_DEVICE
            )
        else:
            self.embedding_service = embedding_service

        logger.info("RAG Service initialized")

    def search(
        self,
        query: str,
        top_k: int = 5,
        language: Optional[str] = None,
        category: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search

        Args:
            query: Search query
            top_k: Number of results
            language: Filter by language
            category: Filter by category
            year_min: Minimum year
            year_max: Maximum year
            threshold: Minimum similarity threshold

        Returns:
            List of search results
        """
        try:
            # Search using ChromaDB (it handles embeddings internally)
            results = self.vector_store.search_with_filters(
                query_text=query,
                n_results=top_k,
                language=language,
                category=category,
                year_min=year_min,
                year_max=year_max
            )

            # Apply threshold if specified
            if threshold is not None:
                results = [r for r in results if r['score'] >= threshold]

            # Convert to SearchResult objects
            search_results = []
            for result in results:
                meta = result['metadata']
                search_results.append(SearchResult(
                    chunk_id=meta.get('chunk_id', 0),
                    act_number=meta.get('act_number', 0),
                    title=meta.get('title', ''),
                    content=result['document'],
                    section=meta.get('section_title'),
                    score=result['score'],
                    metadata={
                        'year': meta.get('year'),
                        'category': meta.get('category'),
                        'section_number': meta.get('section_number'),
                        'language': meta.get('language')
                    }
                ))

            logger.info(f"Search for '{query}' returned {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def search_from_request(self, request: SearchRequest) -> SearchResponse:
        """
        Perform search from SearchRequest object

        Args:
            request: Search request

        Returns:
            Search response with results and metadata
        """
        start_time = datetime.utcnow()

        # Extract filters
        language = None
        category = None
        year_min = None
        year_max = None

        if request.filters:
            language = request.filters.get('language')
            category = request.filters.get('category')
            year_min = request.filters.get('year_min')
            year_max = request.filters.get('year_max')

        # Override with request language if provided
        if request.language:
            language = request.language

        # Perform search
        results = self.search(
            query=request.query,
            top_k=request.top_k,
            language=language,
            category=category,
            year_min=year_min,
            year_max=year_max,
            threshold=request.threshold
        )

        end_time = datetime.utcnow()
        search_time = (end_time - start_time).total_seconds() * 1000

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_time_ms=search_time,
            timestamp=end_time
        )

    def add_documents(
        self,
        chunk_ids: List[int],
        texts: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> bool:
        """
        Add documents to vector store

        Args:
            chunk_ids: List of chunk IDs
            texts: List of text content
            metadatas: List of metadata dictionaries

        Returns:
            Success status
        """
        try:
            success = self.vector_store.add_documents(
                chunk_ids=chunk_ids,
                texts=texts,
                metadatas=metadatas
            )

            if success:
                logger.info(f"Added {len(chunk_ids)} documents to RAG system")

            return success

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False

    def get_document(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID

        Args:
            chunk_id: Chunk ID

        Returns:
            Document data or None
        """
        return self.vector_store.get_by_id(chunk_id)

    def delete_documents(self, chunk_ids: List[int]) -> bool:
        """
        Delete documents from vector store

        Args:
            chunk_ids: List of chunk IDs

        Returns:
            Success status
        """
        return self.vector_store.delete_by_id(chunk_ids)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get RAG system statistics

        Returns:
            Statistics dictionary
        """
        vector_stats = self.vector_store.get_stats()
        embedding_info = self.embedding_service.get_model_info()

        return {
            'vector_store': vector_stats,
            'embedding_model': embedding_info,
            'status': 'operational'
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of RAG system

        Returns:
            Health status dictionary
        """
        try:
            stats = self.vector_store.get_stats()
            total_docs = stats.get('total_documents', 0)

            return {
                'status': 'healthy',
                'vector_store': 'operational',
                'embedding_service': 'operational',
                'total_documents': total_docs
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
