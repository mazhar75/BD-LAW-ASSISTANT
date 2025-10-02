"""
Embedding Service
Handles text embedding generation using Sentence Transformers
"""
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union, Optional
import logging
import torch

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using Sentence Transformers"""

    # Recommended models for different use cases
    MODELS = {
        'multilingual': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',  # 768 dims
        'multilingual-mini': 'paraphrase-multilingual-MiniLM-L12-v2',  # 384 dims (default)
        'english': 'sentence-transformers/all-mpnet-base-v2',  # 768 dims
        'english-mini': 'sentence-transformers/all-MiniLM-L6-v2',  # 384 dims
        'legal': 'BAAI/bge-base-en-v1.5',  # 768 dims, domain-specific
    }

    def __init__(
        self,
        model_name: str = 'multilingual-mini',
        device: Optional[str] = None,
        batch_size: int = 32
    ):
        """
        Initialize embedding service

        Args:
            model_name: Name of the model (from MODELS dict or custom)
            device: Device to run on ('cuda', 'cpu', or None for auto)
            batch_size: Batch size for encoding
        """
        # Select model
        if model_name in self.MODELS:
            self.model_name = self.MODELS[model_name]
        else:
            self.model_name = model_name

        self.batch_size = batch_size

        # Set device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device

        # Load model
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(
            self.model_name,
            device=self.device
        )

        # Get embedding dimension
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Dimension: {self.dimension}, Device: {self.device}")

    def generate(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        show_progress: bool = False
    ) -> np.ndarray:
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
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )

            logger.debug(f"Generated {len(texts)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def generate_single(
        self,
        text: str,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed
            normalize: Whether to normalize

        Returns:
            1D embedding array
        """
        embedding = self.generate([text], normalize=normalize)
        return embedding[0]

    def generate_query_embedding(
        self,
        query: str,
        normalize: bool = True
    ) -> np.ndarray:
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
            return embedding[0]
        else:
            return self.generate_single(query, normalize=normalize)

    def generate_batch(
        self,
        texts: List[str],
        normalize: bool = True,
        max_length: Optional[int] = None,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Generate embeddings in batches with optional truncation

        Args:
            texts: List of texts
            normalize: Whether to normalize
            max_length: Maximum text length (chars)
            show_progress: Show progress bar

        Returns:
            Array of embeddings
        """
        # Truncate if needed
        if max_length:
            texts = [text[:max_length] for text in texts]

        return self.generate(texts, normalize=normalize, show_progress=show_progress)

    def compute_similarity(
        self,
        text1: Union[str, np.ndarray],
        text2: Union[str, np.ndarray],
        metric: str = 'cosine'
    ) -> float:
        """
        Compute similarity between two texts or embeddings

        Args:
            text1: First text or embedding
            text2: Second text or embedding
            metric: Similarity metric ('cosine', 'euclidean', 'dot')

        Returns:
            Similarity score
        """
        # Generate embeddings if needed
        if isinstance(text1, str):
            emb1 = self.generate_single(text1, normalize=(metric == 'cosine'))
        else:
            emb1 = text1

        if isinstance(text2, str):
            emb2 = self.generate_single(text2, normalize=(metric == 'cosine'))
        else:
            emb2 = text2

        # Compute similarity
        if metric == 'cosine' or metric == 'dot':
            # Dot product (cosine if normalized)
            similarity = float(np.dot(emb1, emb2))
        elif metric == 'euclidean':
            # Negative euclidean distance
            similarity = -float(np.linalg.norm(emb1 - emb2))
        else:
            raise ValueError(f"Unknown metric: {metric}")

        return similarity

    def compute_similarity_batch(
        self,
        query: Union[str, np.ndarray],
        texts: Union[List[str], np.ndarray],
        metric: str = 'cosine'
    ) -> np.ndarray:
        """
        Compute similarity between a query and multiple texts

        Args:
            query: Query text or embedding
            texts: List of texts or embeddings array
            metric: Similarity metric

        Returns:
            Array of similarity scores
        """
        # Generate embeddings if needed
        if isinstance(query, str):
            query_emb = self.generate_single(query, normalize=(metric == 'cosine'))
        else:
            query_emb = query

        if isinstance(texts, list):
            text_embs = self.generate(texts, normalize=(metric == 'cosine'))
        else:
            text_embs = texts

        # Compute similarities
        if metric == 'cosine' or metric == 'dot':
            similarities = np.dot(text_embs, query_emb)
        elif metric == 'euclidean':
            similarities = -np.linalg.norm(text_embs - query_emb, axis=1)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        return similarities

    def get_model_info(self) -> dict:
        """
        Get information about the model

        Returns:
            Model information dictionary
        """
        return {
            'model_name': self.model_name,
            'dimension': self.dimension,
            'device': self.device,
            'batch_size': self.batch_size,
            'max_seq_length': getattr(self.model, 'max_seq_length', 512),
        }

    @staticmethod
    def list_available_models() -> dict:
        """
        List available pre-configured models

        Returns:
            Dictionary of model names and paths
        """
        return EmbeddingService.MODELS

    def __repr__(self) -> str:
        return f"EmbeddingService(model={self.model_name}, dim={self.dimension}, device={self.device})"
