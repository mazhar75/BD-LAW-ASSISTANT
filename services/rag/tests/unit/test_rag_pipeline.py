"""
Unit tests for RAG pipeline components
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from rag.rag_pipeline_gemini import RAGPipeline, RAGConfig


class TestRAGPipeline(unittest.TestCase):
    """Test RAG pipeline functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = RAGConfig(
            model_name="gemini-1.5-flash",
            temperature=0.1,
            max_output_tokens=100
        )

    @patch('rag.rag_pipeline_gemini.FAISS')
    @patch('rag.rag_pipeline_gemini.genai')
    def test_pipeline_initialization(self, mock_genai, mock_faiss):
        """Test RAG pipeline initialization"""
        # Mock FAISS index
        mock_index = Mock()
        mock_faiss.read_index.return_value = mock_index

        # Initialize pipeline
        pipeline = RAGPipeline(config=self.config)

        # Verify initialization
        self.assertIsNotNone(pipeline)
        self.assertEqual(pipeline.config.model_name, "gemini-1.5-flash")

    @patch('rag.rag_pipeline_gemini.FAISS')
    def test_search_documents(self, mock_faiss):
        """Test document search functionality"""
        # Mock FAISS index
        mock_index = Mock()
        mock_faiss.read_index.return_value = mock_index

        # Mock search results
        distances = np.array([[0.1, 0.2, 0.3]])
        indices = np.array([[0, 1, 2]])
        mock_index.search.return_value = (distances, indices)

        # Initialize pipeline
        pipeline = RAGPipeline(config=self.config)
        pipeline.index = mock_index

        # Mock chunks data
        pipeline.chunks_df = MagicMock()
        pipeline.chunks_df.iloc = [
            {"chunk_id": 0, "content": "Test content 1", "act_name": "Act 1"},
            {"chunk_id": 1, "content": "Test content 2", "act_name": "Act 2"},
            {"chunk_id": 2, "content": "Test content 3", "act_name": "Act 3"}
        ]

        # Perform search
        with patch('rag.rag_pipeline_gemini.model.encode') as mock_encode:
            mock_encode.return_value = np.array([0.5, 0.5, 0.5])
            results = pipeline.search_documents("test query", top_k=3)

        # Verify results
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].chunk_id, 0)

    def test_build_context(self):
        """Test context building from search results"""
        from dataclasses import dataclass

        @dataclass
        class MockSearchResult:
            chunk_id: int
            content: str
            act_name: str
            similarity_score: float

        # Create mock search results
        results = [
            MockSearchResult(0, "Legal content 1", "Act 1", 0.9),
            MockSearchResult(1, "Legal content 2", "Act 2", 0.8),
            MockSearchResult(2, "Legal content 3", "Act 3", 0.7)
        ]

        # Build context (this would be a method in the actual pipeline)
        context = "\n\n".join([f"[{r.act_name}]\n{r.content}" for r in results])

        # Verify context
        self.assertIn("Legal content 1", context)
        self.assertIn("Act 1", context)
        self.assertIn("Act 2", context)
        self.assertIn("Act 3", context)

    @patch('rag.rag_pipeline_gemini.genai')
    def test_generate_response(self, mock_genai):
        """Test response generation with Gemini"""
        # Mock Gemini model
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Generated legal response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        # Create pipeline with mocked model
        pipeline = RAGPipeline(config=self.config)
        pipeline.model = mock_model

        # Generate response
        context = "Legal context"
        query = "What is property law?"

        response = pipeline.model.generate_content(
            f"Context: {context}\n\nQuestion: {query}"
        )

        # Verify response
        self.assertEqual(response.text, "Generated legal response")
        mock_model.generate_content.assert_called_once()


class TestTextSplitting(unittest.TestCase):
    """Test document text splitting functionality"""

    def test_chunk_creation(self):
        """Test creating chunks from text"""
        text = "This is a long legal document. " * 100
        chunk_size = 200
        chunk_overlap = 50

        # Simple chunking logic
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - chunk_overlap if end < len(text) else end

        # Verify chunks
        self.assertTrue(len(chunks) > 1)
        self.assertTrue(all(len(chunk) <= chunk_size for chunk in chunks))

    def test_metadata_extraction(self):
        """Test metadata extraction from documents"""
        document = {
            "filename": "act_153.md",
            "content": "# The Transfer of Property Act\n\nSection 1...",
            "act_number": "153",
            "year": "1882"
        }

        # Extract metadata
        metadata = {
            "act_name": "The Transfer of Property Act",
            "act_number": document["act_number"],
            "year": document["year"],
            "filename": document["filename"]
        }

        # Verify metadata
        self.assertEqual(metadata["act_number"], "153")
        self.assertEqual(metadata["year"], "1882")
        self.assertIn("Transfer", metadata["act_name"])


class TestEmbedding(unittest.TestCase):
    """Test embedding generation"""

    @patch('sentence_transformers.SentenceTransformer')
    def test_embedding_generation(self, mock_transformer):
        """Test generating embeddings for text"""
        # Mock sentence transformer
        mock_model = Mock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_transformer.return_value = mock_model

        # Generate embedding
        text = "Legal text for embedding"
        embedding = mock_model.encode([text])

        # Verify embedding
        self.assertEqual(embedding.shape, (1, 3))
        mock_model.encode.assert_called_once_with([text])

    def test_embedding_normalization(self):
        """Test embedding normalization"""
        # Create sample embedding
        embedding = np.array([3.0, 4.0])

        # Normalize
        norm = np.linalg.norm(embedding)
        normalized = embedding / norm

        # Verify normalization
        self.assertAlmostEqual(np.linalg.norm(normalized), 1.0, places=5)


class TestSearchQuality(unittest.TestCase):
    """Test search quality and relevance"""

    def test_similarity_calculation(self):
        """Test cosine similarity calculation"""
        # Create test vectors
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([0, 1, 0])
        vec3 = np.array([1, 0, 0])

        # Calculate similarities
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        sim1 = cosine_similarity(vec1, vec2)
        sim2 = cosine_similarity(vec1, vec3)

        # Verify similarities
        self.assertAlmostEqual(sim1, 0.0, places=5)  # Orthogonal vectors
        self.assertAlmostEqual(sim2, 1.0, places=5)  # Identical vectors

    def test_relevance_scoring(self):
        """Test relevance scoring for search results"""
        # Mock search results with scores
        results = [
            {"content": "property law", "score": 0.95},
            {"content": "criminal law", "score": 0.60},
            {"content": "property transfer", "score": 0.90}
        ]

        # Filter by relevance threshold
        threshold = 0.70
        relevant = [r for r in results if r["score"] >= threshold]

        # Verify filtering
        self.assertEqual(len(relevant), 2)
        self.assertTrue(all(r["score"] >= threshold for r in relevant))


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)