"""
Embedding Generator using Sentence Transformers
"""
import numpy as np
from typing import List, Union, Optional
import logging
from pathlib import Path
import torch

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not installed. Install with: pip install sentence-transformers")

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings using sentence-transformers"""

    # Recommended models for different use cases
    MODELS = {
        'multilingual': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',  # 768 dims
        'multilingual-mini': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',  # 384 dims
        'english': 'sentence-transformers/all-mpnet-base-v2',  # 768 dims
        'english-mini': 'sentence-transformers/all-MiniLM-L6-v2',  # 384 dims
        'legal': 'BAAI/bge-base-en-v1.5',  # 768 dims, good for domain-specific
        'bengali': 'l3cube-pune/bengali-sentence-similarity-sbert',  # 768 dims, Bengali-specific
    }

    def __init__(self,
                 model_name: str = 'multilingual-mini',
                 device: Optional[str] = None,
                 cache_dir: Optional[str] = None,
                 batch_size: int = 32):
        """
        Initialize embedding generator

        Args:
            model_name: Name or path of the model
            device: Device to run on ('cuda', 'cpu', or None for auto)
            cache_dir: Directory to cache models
            batch_size: Batch size for encoding
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers is not installed")

        # Select model
        if model_name in self.MODELS:
            model_name = self.MODELS[model_name]

        self.model_name = model_name
        self.batch_size = batch_size

        # Set device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device

        # Load model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(
            model_name,
            device=self.device,
            cache_folder=cache_dir
        )

        # Get embedding dimension
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Dimension: {self.dimension}, Device: {self.device}")

    def generate(self,
                 texts: Union[str, List[str]],
                 normalize: bool = True,
                 show_progress: bool = False) -> np.ndarray:
        """
        Generate embeddings for texts

        Args:
            texts: Single text or list of texts
            normalize: Whether to normalize embeddings (for cosine similarity)
            show_progress: Show progress bar

        Returns:
            Numpy array of embeddings
        """
        # Handle single text
        if isinstance(texts, str):
            texts = [texts]

        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )

        return embeddings

    def generate_query_embedding(self,
                                  query: str,
                                  normalize: bool = True) -> np.ndarray:
        """
        Generate embedding for a query (may use special query prefix)

        Args:
            query: Query text
            normalize: Whether to normalize

        Returns:
            Query embedding
        """
        # Some models have special query encoding
        if hasattr(self.model, 'encode_queries'):
            embedding = self.model.encode_queries(
                [query],
                normalize_embeddings=normalize,
                convert_to_numpy=True
            )
        else:
            embedding = self.generate(query, normalize=normalize)

        return embedding[0] if embedding.ndim > 1 else embedding

    def generate_batch(self,
                       texts: List[str],
                       normalize: bool = True,
                       max_length: Optional[int] = None) -> List[np.ndarray]:
        """
        Generate embeddings in batches with optional truncation

        Args:
            texts: List of texts
            normalize: Whether to normalize
            max_length: Maximum text length (chars)

        Returns:
            List of embeddings
        """
        # Truncate if needed
        if max_length:
            texts = [text[:max_length] for text in texts]

        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            embeddings = self.generate(batch, normalize=normalize)
            all_embeddings.append(embeddings)

        return np.vstack(all_embeddings) if all_embeddings else np.array([])

    def compute_similarity(self,
                           text1: Union[str, List[str]],
                           text2: Union[str, List[str]],
                           metric: str = 'cosine') -> np.ndarray:
        """
        Compute similarity between texts

        Args:
            text1: First text(s)
            text2: Second text(s)
            metric: Similarity metric ('cosine', 'euclidean', 'dot')

        Returns:
            Similarity scores
        """
        # Generate embeddings
        emb1 = self.generate(text1, normalize=(metric == 'cosine'))
        emb2 = self.generate(text2, normalize=(metric == 'cosine'))

        # Ensure 2D arrays
        if emb1.ndim == 1:
            emb1 = emb1.reshape(1, -1)
        if emb2.ndim == 1:
            emb2 = emb2.reshape(1, -1)

        # Compute similarity
        if metric == 'cosine' or metric == 'dot':
            # Dot product (cosine if normalized)
            similarity = np.dot(emb1, emb2.T)
        elif metric == 'euclidean':
            # Negative euclidean distance
            similarity = -np.linalg.norm(emb1[:, np.newaxis] - emb2, axis=2)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        return similarity

    def save_model(self, path: str):
        """Save the model to disk"""
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(str(save_path))
        logger.info(f"Model saved to {save_path}")

    def get_model_info(self) -> dict:
        """Get information about the model"""
        return {
            'model_name': self.model_name,
            'dimension': self.dimension,
            'device': self.device,
            'max_seq_length': getattr(self.model, 'max_seq_length', 512),
            'tokenizer': getattr(self.model.tokenizer, 'name_or_path', 'unknown')
        }

    @staticmethod
    def list_available_models() -> dict:
        """List available pre-configured models"""
        return EmbeddingGenerator.MODELS

    def benchmark(self, sample_texts: List[str]) -> dict:
        """
        Benchmark embedding generation speed

        Args:
            sample_texts: Sample texts to benchmark

        Returns:
            Benchmark results
        """
        import time

        # Single text
        start = time.time()
        _ = self.generate(sample_texts[0])
        single_time = time.time() - start

        # Batch
        start = time.time()
        _ = self.generate(sample_texts)
        batch_time = time.time() - start

        # Similarity
        start = time.time()
        _ = self.compute_similarity(sample_texts[0], sample_texts[1])
        sim_time = time.time() - start

        return {
            'single_encoding_ms': single_time * 1000,
            'batch_encoding_ms': batch_time * 1000,
            'texts_per_second': len(sample_texts) / batch_time,
            'similarity_computation_ms': sim_time * 1000,
            'model': self.model_name,
            'device': self.device
        }