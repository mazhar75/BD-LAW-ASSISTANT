"""
FAISS Vector Store for similarity search
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
import pickle
from pathlib import Path
import logging

try:
    import faiss
except ImportError:
    faiss = None
    print("Warning: FAISS not installed. Install with: pip install faiss-cpu")

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store for semantic search"""

    def __init__(self,
                 dimension: int = 384,
                 index_type: str = "Flat",
                 metric: str = "cosine",
                 store_path: Optional[str] = None):
        """
        Initialize vector store

        Args:
            dimension: Vector dimension (depends on embedding model)
            index_type: FAISS index type (Flat, IVF, HNSW)
            metric: Distance metric (cosine, euclidean)
            store_path: Path to save/load index
        """
        if faiss is None:
            raise ImportError("FAISS is not installed")

        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        self.store_path = Path(store_path) if store_path else Path("vector_store.faiss")

        # Initialize index
        self.index = self._create_index()

        # Metadata storage (maps index ID to chunk ID)
        self.metadata: List[Dict] = []

        # ID mapping
        self.id_to_index: Dict[int, int] = {}

        logger.info(f"Vector store initialized: dim={dimension}, type={index_type}, metric={metric}")

    def _create_index(self):
        """Create FAISS index based on configuration"""
        if self.metric == "cosine":
            # For cosine similarity, we normalize vectors and use inner product
            if self.index_type == "Flat":
                index = faiss.IndexFlatIP(self.dimension)
            elif self.index_type == "IVF":
                quantizer = faiss.IndexFlatIP(self.dimension)
                index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            elif self.index_type == "HNSW":
                index = faiss.IndexHNSWFlat(self.dimension, 32)
            else:
                raise ValueError(f"Unknown index type: {self.index_type}")
        else:
            # For Euclidean distance
            if self.index_type == "Flat":
                index = faiss.IndexFlatL2(self.dimension)
            elif self.index_type == "IVF":
                quantizer = faiss.IndexFlatL2(self.dimension)
                index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            else:
                raise ValueError(f"Unknown index type: {self.index_type}")

        return index

    def add_vectors(self,
                    vectors: np.ndarray,
                    metadata: List[Dict],
                    chunk_ids: Optional[List[int]] = None):
        """
        Add vectors to the index

        Args:
            vectors: Numpy array of vectors (n_vectors, dimension)
            metadata: List of metadata dictionaries for each vector
            chunk_ids: Optional list of chunk IDs
        """
        if vectors.shape[1] != self.dimension:
            raise ValueError(f"Vector dimension {vectors.shape[1]} != expected {self.dimension}")

        # Normalize vectors for cosine similarity
        if self.metric == "cosine":
            vectors = self._normalize_vectors(vectors)

        # Train index if needed (for IVF)
        if self.index_type == "IVF" and not self.index.is_trained:
            logger.info("Training IVF index...")
            self.index.train(vectors)

        # Add vectors to index
        start_idx = self.index.ntotal
        self.index.add(vectors)

        # Store metadata
        for i, meta in enumerate(metadata):
            idx = start_idx + i
            self.metadata.append(meta)
            if chunk_ids and i < len(chunk_ids):
                self.id_to_index[chunk_ids[i]] = idx

        logger.info(f"Added {len(vectors)} vectors to index (total: {self.index.ntotal})")

    def search(self,
               query_vector: np.ndarray,
               k: int = 5,
               threshold: Optional[float] = None) -> List[Tuple[int, float, Dict]]:
        """
        Search for similar vectors

        Args:
            query_vector: Query vector
            k: Number of results to return
            threshold: Optional similarity threshold

        Returns:
            List of tuples (index, score, metadata)
        """
        if query_vector.shape[0] != self.dimension:
            raise ValueError(f"Query dimension {query_vector.shape[0]} != expected {self.dimension}")

        # Normalize for cosine similarity
        if self.metric == "cosine":
            query_vector = self._normalize_vectors(query_vector.reshape(1, -1))
        else:
            query_vector = query_vector.reshape(1, -1)

        # Search
        scores, indices = self.index.search(query_vector, k)

        # Format results
        results = []
        for i, (idx, score) in enumerate(zip(indices[0], scores[0])):
            if idx == -1:  # FAISS returns -1 for empty results
                continue

            if threshold is not None:
                if self.metric == "cosine" and score < threshold:
                    continue
                elif self.metric != "cosine" and score > threshold:
                    continue

            metadata = self.metadata[idx] if idx < len(self.metadata) else {}
            results.append((idx, float(score), metadata))

        return results

    def search_batch(self,
                     query_vectors: np.ndarray,
                     k: int = 5) -> List[List[Tuple[int, float, Dict]]]:
        """
        Batch search for multiple query vectors

        Args:
            query_vectors: Array of query vectors
            k: Number of results per query

        Returns:
            List of search results for each query
        """
        if self.metric == "cosine":
            query_vectors = self._normalize_vectors(query_vectors)

        scores, indices = self.index.search(query_vectors, k)

        results = []
        for query_idx in range(len(query_vectors)):
            query_results = []
            for i, (idx, score) in enumerate(zip(indices[query_idx], scores[query_idx])):
                if idx == -1:
                    continue
                metadata = self.metadata[idx] if idx < len(self.metadata) else {}
                query_results.append((idx, float(score), metadata))
            results.append(query_results)

        return results

    def remove_vectors(self, indices: List[int]):
        """
        Remove vectors from index (only works with certain index types)

        Args:
            indices: List of indices to remove
        """
        if hasattr(self.index, 'remove_ids'):
            ids = np.array(indices, dtype=np.int64)
            self.index.remove_ids(ids)
            logger.info(f"Removed {len(indices)} vectors from index")
        else:
            logger.warning(f"Index type {self.index_type} does not support removal")

    def save(self, path: Optional[str] = None):
        """
        Save index and metadata to disk

        Args:
            path: Optional path to save to
        """
        save_path = Path(path) if path else self.store_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, str(save_path))

        # Save metadata
        meta_path = save_path.with_suffix('.meta')
        with open(meta_path, 'wb') as f:
            pickle.dump({
                'metadata': self.metadata,
                'id_to_index': self.id_to_index,
                'dimension': self.dimension,
                'index_type': self.index_type,
                'metric': self.metric
            }, f)

        logger.info(f"Saved vector store to {save_path}")

    def load(self, path: Optional[str] = None):
        """
        Load index and metadata from disk

        Args:
            path: Optional path to load from
        """
        load_path = Path(path) if path else self.store_path

        if not load_path.exists():
            raise FileNotFoundError(f"Index file not found: {load_path}")

        # Load FAISS index
        self.index = faiss.read_index(str(load_path))

        # Load metadata
        meta_path = load_path.with_suffix('.meta')
        if meta_path.exists():
            with open(meta_path, 'rb') as f:
                data = pickle.load(f)
                self.metadata = data['metadata']
                self.id_to_index = data['id_to_index']
                self.dimension = data['dimension']
                self.index_type = data['index_type']
                self.metric = data['metric']

        logger.info(f"Loaded vector store from {load_path} ({self.index.ntotal} vectors)")

    def clear(self):
        """Clear all vectors from the index"""
        self.index = self._create_index()
        self.metadata = []
        self.id_to_index = {}
        logger.info("Cleared vector store")

    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'index_type': self.index_type,
            'metric': self.metric,
            'is_trained': getattr(self.index, 'is_trained', True),
            'metadata_count': len(self.metadata)
        }

    @staticmethod
    def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
        """Normalize vectors for cosine similarity"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        # Avoid division by zero
        norms[norms == 0] = 1
        return vectors / norms