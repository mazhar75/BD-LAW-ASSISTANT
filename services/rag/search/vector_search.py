"""
Vector Search - Intelligent search combining FAISS vector store with embeddings
"""
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import logging
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent))

from embeddings.vector_store import VectorStore
from embeddings.embedding_generator import EmbeddingGenerator
from chunking.document_chunker import Chunk
from ingestion.data_loader import Document

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a search result"""
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict
    highlights: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'chunk_id': self.chunk_id,
            'document_id': self.document_id,
            'content': self.content,
            'score': self.score,
            'metadata': self.metadata,
            'highlights': self.highlights
        }


class VectorSearch:
    """Hybrid search engine combining semantic and keyword search"""

    def __init__(self,
                 vector_store: Optional[VectorStore] = None,
                 embedding_generator: Optional[EmbeddingGenerator] = None,
                 dimension: int = 384):
        """
        Initialize vector search

        Args:
            vector_store: Pre-initialized vector store or None to create new
            embedding_generator: Pre-initialized embedding generator or None
            dimension: Vector dimension for embeddings
        """
        # Initialize vector store
        self.vector_store = vector_store or VectorStore(
            dimension=dimension,
            index_type="Flat",  # Use Flat for accuracy in MVP
            metric="cosine"
        )

        # Initialize embedding generator
        self.embedding_generator = embedding_generator or EmbeddingGenerator()

        # Search configuration
        self.default_top_k = 10
        self.reranking_enabled = True

        logger.info(f"VectorSearch initialized with dimension={dimension}")

    def index_chunk(self, chunk: Chunk):
        """
        Index a single chunk

        Args:
            chunk: Chunk to index
        """
        # Generate embedding
        embedding = self.embedding_generator.generate_embedding(chunk.content)

        # Prepare metadata
        metadata = {
            'chunk_id': chunk.chunk_id,
            'document_id': chunk.document_id,
            'chunk_index': chunk.chunk_index,
            **chunk.metadata
        }

        # Add to vector store
        self.vector_store.add_vectors(
            np.array([embedding]),
            [metadata],
            [chunk.chunk_id]
        )

    def index_chunks_batch(self, chunks: List[Chunk], batch_size: int = 32):
        """
        Index multiple chunks in batches

        Args:
            chunks: List of chunks to index
            batch_size: Batch size for embedding generation
        """
        total_chunks = len(chunks)
        logger.info(f"Indexing {total_chunks} chunks in batches of {batch_size}")

        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i+batch_size]

            # Generate embeddings for batch
            texts = [chunk.content for chunk in batch]
            embeddings = self.embedding_generator.generate_embeddings_batch(texts)

            # Prepare metadata
            metadata_list = []
            chunk_ids = []
            for chunk in batch:
                metadata = {
                    'chunk_id': chunk.chunk_id,
                    'document_id': chunk.document_id,
                    'chunk_index': chunk.chunk_index,
                    'content': chunk.content,  # Store content for retrieval
                    **chunk.metadata
                }
                metadata_list.append(metadata)
                chunk_ids.append(chunk.chunk_id)

            # Add to vector store
            self.vector_store.add_vectors(embeddings, metadata_list, chunk_ids)

            if (i + batch_size) % 100 == 0:
                logger.info(f"Indexed {min(i+batch_size, total_chunks)}/{total_chunks} chunks")

        logger.info(f"Successfully indexed {total_chunks} chunks")

    def semantic_search(self,
                       query: str,
                       top_k: int = 10,
                       threshold: Optional[float] = None) -> List[SearchResult]:
        """
        Perform semantic vector search

        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Optional similarity threshold

        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_query_embedding(query)

        # Search in vector store
        results = self.vector_store.search(
            query_embedding,
            k=top_k,
            threshold=threshold
        )

        # Convert to SearchResult objects
        search_results = []
        for idx, score, metadata in results:
            result = SearchResult(
                chunk_id=metadata.get('chunk_id', ''),
                document_id=metadata.get('document_id', ''),
                content=metadata.get('content', ''),
                score=score,
                metadata=metadata
            )
            search_results.append(result)

        return search_results

    def keyword_search(self,
                      query: str,
                      chunks_metadata: List[Dict],
                      top_k: int = 10) -> List[SearchResult]:
        """
        Perform keyword-based search

        Args:
            query: Search query
            chunks_metadata: List of chunk metadata to search
            top_k: Number of results to return

        Returns:
            List of search results
        """
        # Tokenize query
        query_terms = set(query.lower().split())

        # Score each chunk based on keyword matches
        scored_chunks = []
        for metadata in chunks_metadata:
            content = metadata.get('content', '').lower()
            title = metadata.get('title', '').lower()

            # Calculate keyword match score
            content_score = sum(1 for term in query_terms if term in content)
            title_score = sum(2 for term in query_terms if term in title)  # Title matches weighted higher
            total_score = content_score + title_score

            if total_score > 0:
                scored_chunks.append((total_score, metadata))

        # Sort by score and take top_k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored_chunks[:top_k]

        # Convert to SearchResult objects
        search_results = []
        for score, metadata in top_chunks:
            result = SearchResult(
                chunk_id=metadata.get('chunk_id', ''),
                document_id=metadata.get('document_id', ''),
                content=metadata.get('content', ''),
                score=float(score),
                metadata=metadata
            )
            search_results.append(result)

        return search_results

    def hybrid_search(self,
                     query: str,
                     top_k: int = 10,
                     semantic_weight: float = 0.7,
                     keyword_weight: float = 0.3) -> List[SearchResult]:
        """
        Perform hybrid search combining semantic and keyword search

        Args:
            query: Search query
            top_k: Number of results to return
            semantic_weight: Weight for semantic search scores
            keyword_weight: Weight for keyword search scores

        Returns:
            List of search results
        """
        # Get semantic search results
        semantic_results = self.semantic_search(query, top_k=top_k*2)

        # Get all metadata for keyword search
        all_metadata = self.vector_store.metadata

        # Get keyword search results
        keyword_results = self.keyword_search(query, all_metadata, top_k=top_k*2)

        # Combine and re-rank results
        combined_scores = defaultdict(lambda: {'semantic': 0.0, 'keyword': 0.0})

        # Add semantic scores
        for result in semantic_results:
            combined_scores[result.chunk_id]['semantic'] = result.score
            combined_scores[result.chunk_id]['result'] = result

        # Add keyword scores (normalized)
        max_keyword_score = max([r.score for r in keyword_results]) if keyword_results else 1.0
        for result in keyword_results:
            normalized_score = result.score / max_keyword_score if max_keyword_score > 0 else 0
            combined_scores[result.chunk_id]['keyword'] = normalized_score
            if 'result' not in combined_scores[result.chunk_id]:
                combined_scores[result.chunk_id]['result'] = result

        # Calculate final scores
        final_results = []
        for chunk_id, scores in combined_scores.items():
            final_score = (
                scores['semantic'] * semantic_weight +
                scores['keyword'] * keyword_weight
            )
            result = scores['result']
            result.score = final_score
            final_results.append(result)

        # Sort by final score
        final_results.sort(key=lambda x: x.score, reverse=True)

        return final_results[:top_k]

    def search_with_filters(self,
                           query: str,
                           filters: Optional[Dict] = None,
                           top_k: int = 10,
                           search_type: str = 'hybrid') -> List[SearchResult]:
        """
        Search with metadata filters

        Args:
            query: Search query
            filters: Metadata filters (e.g., {'language': 'en', 'year': 2020})
            top_k: Number of results to return
            search_type: Type of search ('semantic', 'keyword', or 'hybrid')

        Returns:
            Filtered search results
        """
        # Perform base search
        if search_type == 'semantic':
            results = self.semantic_search(query, top_k=top_k*3)  # Get more for filtering
        elif search_type == 'keyword':
            results = self.keyword_search(query, self.vector_store.metadata, top_k=top_k*3)
        else:
            results = self.hybrid_search(query, top_k=top_k*3)

        # Apply filters if provided
        if filters:
            filtered_results = []
            for result in results:
                match = True
                for key, value in filters.items():
                    if key in result.metadata:
                        # Handle different filter types
                        if key == 'year' and isinstance(value, dict):
                            # Range filter
                            year = result.metadata.get('year')
                            if year:
                                if 'min' in value and year < value['min']:
                                    match = False
                                if 'max' in value and year > value['max']:
                                    match = False
                        elif result.metadata[key] != value:
                            match = False
                if match:
                    filtered_results.append(result)
            results = filtered_results

        return results[:top_k]

    def rerank_results(self,
                      query: str,
                      results: List[SearchResult],
                      method: str = 'relevance') -> List[SearchResult]:
        """
        Re-rank search results

        Args:
            query: Original query
            results: Search results to re-rank
            method: Re-ranking method ('relevance', 'recency', 'popularity')

        Returns:
            Re-ranked results
        """
        if method == 'relevance':
            # Re-rank based on query term coverage
            query_terms = set(query.lower().split())

            for result in results:
                content_lower = result.content.lower()
                # Calculate coverage score
                coverage = sum(1 for term in query_terms if term in content_lower)
                coverage_ratio = coverage / len(query_terms) if query_terms else 0

                # Boost score based on coverage
                result.score *= (1 + coverage_ratio * 0.5)

            # Re-sort by new scores
            results.sort(key=lambda x: x.score, reverse=True)

        elif method == 'recency':
            # Re-rank based on year (more recent = higher)
            for result in results:
                year = result.metadata.get('year')
                if year:
                    # Boost recent documents
                    recency_boost = (year - 1800) / 200  # Normalize to 0-1 range
                    result.score *= (1 + recency_boost * 0.3)

            results.sort(key=lambda x: x.score, reverse=True)

        return results

    def extract_highlights(self,
                          query: str,
                          content: str,
                          max_highlights: int = 3,
                          context_window: int = 50) -> List[str]:
        """
        Extract highlighted snippets from content

        Args:
            query: Search query
            content: Content to extract highlights from
            max_highlights: Maximum number of highlights
            context_window: Characters of context around match

        Returns:
            List of highlighted snippets
        """
        query_terms = query.lower().split()
        content_lower = content.lower()
        highlights = []

        for term in query_terms:
            if term in content_lower:
                # Find all occurrences
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                matches = pattern.finditer(content)

                for match in matches:
                    if len(highlights) >= max_highlights:
                        break

                    start = max(0, match.start() - context_window)
                    end = min(len(content), match.end() + context_window)

                    # Extract snippet
                    snippet = content[start:end]
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(content):
                        snippet = snippet + "..."

                    highlights.append(snippet)

        return highlights[:max_highlights]

    def search(self,
              query: str,
              top_k: Optional[int] = None,
              filters: Optional[Dict] = None,
              search_type: str = 'hybrid',
              include_highlights: bool = True) -> List[SearchResult]:
        """
        Main search interface

        Args:
            query: Search query
            top_k: Number of results (defaults to self.default_top_k)
            filters: Optional metadata filters
            search_type: Type of search to perform
            include_highlights: Whether to include text highlights

        Returns:
            List of search results
        """
        top_k = top_k or self.default_top_k

        # Perform search with filters
        results = self.search_with_filters(
            query, filters, top_k, search_type
        )

        # Re-rank if enabled
        if self.reranking_enabled:
            results = self.rerank_results(query, results)

        # Add highlights if requested
        if include_highlights:
            for result in results:
                result.highlights = self.extract_highlights(
                    query, result.content
                )

        return results

    def save_index(self, path: Optional[str] = None):
        """Save the vector index to disk"""
        self.vector_store.save(path)
        logger.info(f"Index saved to {path or 'default location'}")

    def load_index(self, path: Optional[str] = None):
        """Load the vector index from disk"""
        self.vector_store.load(path)
        logger.info(f"Index loaded from {path or 'default location'}")

    def get_statistics(self) -> Dict:
        """Get search index statistics"""
        stats = self.vector_store.get_stats()
        stats['search_type'] = 'hybrid'
        stats['reranking_enabled'] = self.reranking_enabled
        return stats


def main():
    """Test vector search functionality"""
    from ingestion.data_loader import DataLoader
    from chunking.document_chunker import DocumentChunker

    # Initialize components
    loader = DataLoader()
    chunker = DocumentChunker()
    search_engine = VectorSearch()

    print("Vector Search Test")
    print("=" * 60)

    # Load and chunk a few documents
    print("\n1. Loading and indexing documents...")
    chunks_to_index = []

    for doc in loader.load_acts(limit=3):
        chunks = chunker.chunk_legal_document(
            doc.act_number,
            doc.title,
            doc.content,
            doc.language
        )
        chunks_to_index.extend(chunks)

    print(f"   Created {len(chunks_to_index)} chunks from 3 documents")

    # Index chunks
    print("\n2. Indexing chunks...")
    search_engine.index_chunks_batch(chunks_to_index)
    print(f"   Indexed {len(chunks_to_index)} chunks")

    # Test searches
    test_queries = [
        "lawful government notification",
        "act provisions",
        "legal authority"
    ]

    print("\n3. Testing search queries:")
    for query in test_queries:
        print(f"\n   Query: '{query}'")

        # Semantic search
        semantic_results = search_engine.semantic_search(query, top_k=3)
        print(f"   Semantic: Found {len(semantic_results)} results")

        # Hybrid search
        hybrid_results = search_engine.hybrid_search(query, top_k=3)
        print(f"   Hybrid: Found {len(hybrid_results)} results")

        if hybrid_results:
            print(f"   Top result preview: {hybrid_results[0].content[:100]}...")

    # Test with filters
    print("\n4. Testing filtered search:")
    filtered_results = search_engine.search_with_filters(
        "law",
        filters={'language': 'en'},
        top_k=5
    )
    print(f"   Found {len(filtered_results)} English documents")

    # Get statistics
    print("\n5. Index statistics:")
    stats = search_engine.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    main()