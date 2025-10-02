"""
ChromaDB Vector Store Implementation
Provides vector storage and semantic search using ChromaDB
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """ChromaDB-based vector store for semantic search"""

    def __init__(
        self,
        collection_name: str = "bd_laws_v1",
        persist_directory: str = "./data/chroma_data",
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2",
        distance_metric: str = "cosine"
    ):
        """
        Initialize ChromaDB vector store

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory for persistent storage
            embedding_model: Sentence transformer model name
            distance_metric: Distance metric (cosine, l2, ip)
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.distance_metric = distance_metric
        self.embedding_model = embedding_model

        # Create persist directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client (new API for v1.1.0+)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )

        # Create embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )

        # Get or create collection
        self.collection = self._get_or_create_collection()

        logger.info(f"ChromaDB initialized: {collection_name} at {persist_directory}")

    def _get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            # Create new collection
            collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={
                    "hnsw:space": self.distance_metric,
                    "hnsw:construction_ef": 100,
                    "hnsw:search_ef": 100,
                    "hnsw:M": 16
                }
            )
            logger.info(f"Created new collection: {self.collection_name}")

        return collection

    def add_documents(
        self,
        chunk_ids: List[int],
        texts: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> bool:
        """
        Add documents to ChromaDB

        Args:
            chunk_ids: List of chunk IDs
            texts: List of text content
            metadatas: List of metadata dictionaries

        Returns:
            Success status
        """
        try:
            # Validate inputs
            if len(chunk_ids) != len(texts) or len(chunk_ids) != len(metadatas):
                raise ValueError("chunk_ids, texts, and metadatas must have same length")

            # Generate IDs
            ids = [f"chunk_{cid}" for cid in chunk_ids]

            # Add to collection
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )

            logger.info(f"Added {len(chunk_ids)} documents to ChromaDB")
            return True

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False

    def search(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents

        Args:
            query_text: Query text
            n_results: Number of results to return
            where: Metadata filters
            where_document: Document content filters

        Returns:
            List of search results with metadata and scores
        """
        try:
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
                where_document=where_document
            )

            # Format results
            formatted_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'chunk_id': results['metadatas'][0][i].get('chunk_id'),
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'score': 1 - results['distances'][0][i]  # Convert to similarity
                    })

            logger.debug(f"Search returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def search_with_filters(
        self,
        query_text: str,
        n_results: int = 5,
        language: Optional[str] = None,
        category: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search with common filters

        Args:
            query_text: Query text
            n_results: Number of results
            language: Filter by language
            category: Filter by category
            year_min: Minimum year
            year_max: Maximum year

        Returns:
            Filtered search results
        """
        where_filters = {}

        if language:
            where_filters['language'] = language

        if category:
            where_filters['category'] = category

        # Handle year range with $and if both min and max specified
        if year_min and year_max:
            # Need to use $and for range queries
            and_filters = []
            if where_filters:
                for key, value in where_filters.items():
                    and_filters.append({key: value})
                where_filters = {"$and": and_filters + [
                    {"year": {"$gte": year_min}},
                    {"year": {"$lte": year_max}}
                ]}
            else:
                where_filters = {"$and": [
                    {"year": {"$gte": year_min}},
                    {"year": {"$lte": year_max}}
                ]}
        elif year_min:
            where_filters['year'] = {"$gte": year_min}
        elif year_max:
            where_filters['year'] = {"$lte": year_max}

        return self.search(
            query_text=query_text,
            n_results=n_results,
            where=where_filters if where_filters else None
        )

    def get_by_id(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """
        Get document by chunk ID

        Args:
            chunk_id: Chunk ID

        Returns:
            Document data or None
        """
        try:
            result = self.collection.get(
                ids=[f"chunk_{chunk_id}"],
                include=["documents", "metadatas"]
            )

            if result['ids'] and len(result['ids']) > 0:
                return {
                    'id': result['ids'][0],
                    'document': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            return None

        except Exception as e:
            logger.error(f"Get by ID error: {e}")
            return None

    def delete_by_id(self, chunk_ids: List[int]) -> bool:
        """
        Delete documents by chunk IDs

        Args:
            chunk_ids: List of chunk IDs

        Returns:
            Success status
        """
        try:
            ids = [f"chunk_{cid}" for cid in chunk_ids]
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(chunk_ids)} documents")
            return True

        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False

    def update_document(
        self,
        chunk_id: int,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update document text or metadata

        Args:
            chunk_id: Chunk ID
            text: New text content
            metadata: New metadata

        Returns:
            Success status
        """
        try:
            doc_id = f"chunk_{chunk_id}"

            update_params = {"ids": [doc_id]}
            if text:
                update_params["documents"] = [text]
            if metadata:
                update_params["metadatas"] = [metadata]

            self.collection.update(**update_params)
            logger.info(f"Updated document: {chunk_id}")
            return True

        except Exception as e:
            logger.error(f"Update error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics

        Returns:
            Statistics dictionary
        """
        try:
            count = self.collection.count()
            return {
                'collection_name': self.collection_name,
                'total_documents': count,
                'distance_metric': self.distance_metric,
                'embedding_model': self.embedding_model,
                'persist_directory': str(self.persist_directory)
            }
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return {
                'collection_name': self.collection_name,
                'total_documents': 0,
                'error': str(e)
            }

    def clear(self) -> bool:
        """
        Clear all documents from collection

        Returns:
            Success status
        """
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self._get_or_create_collection()
            logger.info(f"Cleared collection: {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"Clear error: {e}")
            return False

    def persist(self) -> bool:
        """
        Persist collection to disk

        Returns:
            Success status
        """
        try:
            # ChromaDB with duckdb+parquet automatically persists
            logger.info("Collection persisted successfully")
            return True
        except Exception as e:
            logger.error(f"Persist error: {e}")
            return False
