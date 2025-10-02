"""
Test suite for RAG pipeline components
Tests without requiring external LLM API keys
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import RAG components
from rag.rag_pipeline import RAGPipeline, RAGConfig, BangladeshLawRetriever
from rag.prompts import PromptSelector, LEGAL_QA_PROMPT
from rag.context_manager import ContextWindowManager, ContextWindow, DocumentRanker


class TestRAGConfig(unittest.TestCase):
    """Test RAG configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = RAGConfig()
        self.assertEqual(config.model_name, "gpt-4-turbo-preview")
        self.assertEqual(config.temperature, 0.1)
        self.assertEqual(config.max_tokens, 2048)
        self.assertEqual(config.top_k, 5)
        self.assertTrue(config.use_memory)

    def test_custom_config(self):
        """Test custom configuration"""
        config = RAGConfig(
            model_name="claude-3",
            temperature=0.5,
            max_tokens=4096,
            streaming=True
        )
        self.assertEqual(config.model_name, "claude-3")
        self.assertEqual(config.temperature, 0.5)
        self.assertEqual(config.max_tokens, 4096)
        self.assertTrue(config.streaming)


class TestPromptSelector(unittest.TestCase):
    """Test prompt selection logic"""

    def test_detect_query_type(self):
        """Test query type detection"""
        selector = PromptSelector()

        # Test comparison detection
        query = "What is the difference between Section 302 and Section 304?"
        self.assertEqual(selector.detect_query_type(query), "comparison")

        # Test summary detection
        query = "Summarize the key points of the Contract Act"
        self.assertEqual(selector.detect_query_type(query), "summary")

        # Test analysis detection
        query = "Analyze the legal implications of this scenario"
        self.assertEqual(selector.detect_query_type(query), "analysis")

        # Test explanation detection
        query = "Explain what Section 420 means"
        self.assertEqual(selector.detect_query_type(query), "explanation")

        # Test Bengali detection
        query = "এই আইনের বাংলা অনুবাদ দিন"
        self.assertEqual(selector.detect_query_type(query), "bengali")

        # Test default QA
        query = "What are the penalties for theft?"
        self.assertEqual(selector.detect_query_type(query), "qa")

    def test_select_prompt(self):
        """Test prompt selection"""
        selector = PromptSelector()

        # Test getting QA prompt
        prompt = selector.select_prompt("qa")
        self.assertEqual(prompt, LEGAL_QA_PROMPT)

        # Test fallback to QA for unknown type
        prompt = selector.select_prompt("unknown_type")
        self.assertEqual(prompt, LEGAL_QA_PROMPT)


class TestContextWindowManager(unittest.TestCase):
    """Test context window management"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = ContextWindow(
            max_tokens=1000,
            max_tokens_per_doc=200,
            preserve_ratio=0.8
        )
        self.manager = ContextWindowManager(self.config)

    def test_token_counting(self):
        """Test token counting functionality"""
        text = "This is a test sentence for counting tokens."
        token_count = self.manager.count_tokens(text)
        self.assertGreater(token_count, 0)
        self.assertLess(token_count, 20)  # Reasonable range for this text

    def test_manage_context(self):
        """Test context management with multiple documents"""
        documents = [
            {
                'content': 'First document content about Bangladesh law section 1.',
                'metadata': {'score': 0.9, 'source': 'doc1'}
            },
            {
                'content': 'Second document with more detailed legal information about contracts and obligations under Bangladesh law.',
                'metadata': {'score': 0.8, 'source': 'doc2'}
            },
            {
                'content': 'Third document containing criminal law provisions and penalties as per Bangladesh Penal Code.',
                'metadata': {'score': 0.7, 'source': 'doc3'}
            }
        ]

        query = "What are the legal provisions?"
        managed_docs = self.manager.manage_context(documents, query)

        # Should return documents that fit within context
        self.assertIsInstance(managed_docs, list)
        self.assertGreater(len(managed_docs), 0)
        self.assertLessEqual(len(managed_docs), len(documents))

    def test_content_truncation(self):
        """Test content truncation"""
        long_content = "Legal text. " * 500  # Create long content
        truncated = self.manager._truncate_content(long_content, 100)

        # Check truncated content is shorter
        truncated_tokens = self.manager.count_tokens(truncated)
        self.assertLessEqual(truncated_tokens, 150)  # Allow some buffer

    def test_smart_truncate_sections(self):
        """Test smart truncation with sections"""
        content = """
        Section 1: Introduction to the law
        This section describes the basic principles.

        Section 2: Key Provisions
        This section contains important legal provisions.

        Article 3: Penalties
        Penalties shall be imposed for violations.

        Section 4: Additional Information
        This contains supplementary details.
        """

        sections = self.manager._split_into_sections(content)
        self.assertGreater(len(sections), 1)

        truncated = self.manager._smart_truncate(sections, 50)
        self.assertIn("Section", truncated)  # Should preserve important sections

    def test_chunk_for_context(self):
        """Test content chunking"""
        content = "This is a long legal document. " * 100
        chunks = self.manager.chunk_for_context(content, chunk_size=50)

        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 1)

        # Each chunk should be within size limit
        for chunk in chunks:
            tokens = self.manager.count_tokens(chunk)
            self.assertLessEqual(tokens, 60)  # Allow small buffer

    def test_cost_estimation(self):
        """Test cost estimation"""
        costs = self.manager.estimate_cost(1000, 500)

        self.assertIn('input_cost', costs)
        self.assertIn('output_cost', costs)
        self.assertIn('total_cost', costs)
        self.assertEqual(costs['input_tokens'], 1000)
        self.assertEqual(costs['output_tokens'], 500)
        self.assertGreater(costs['total_cost'], 0)

    def test_optimize_for_model(self):
        """Test model optimization"""
        self.manager.optimize_for_model("gpt-4-turbo")
        self.assertGreater(self.manager.config.max_tokens, 10000)

        self.manager.optimize_for_model("gpt-3.5-turbo")
        self.assertLess(self.manager.config.max_tokens, 5000)


class TestDocumentRanker(unittest.TestCase):
    """Test document ranking functionality"""

    def test_rank_documents(self):
        """Test document ranking based on relevance"""
        documents = [
            {
                'content': 'Document about property law',
                'metadata': {'score': 0.5, 'year': 2020}
            },
            {
                'content': 'Document about criminal law with exact query match',
                'metadata': {'score': 0.7, 'year': 2022}
            },
            {
                'content': 'General legal document',
                'metadata': {'score': 0.3, 'year': 2010}
            }
        ]

        query = "criminal law"
        ranked = DocumentRanker.rank_documents(documents, query)

        # Document with query match should rank higher
        self.assertEqual(len(ranked), 3)
        self.assertIn('criminal law', ranked[0]['content'])

    def test_importance_markers_boost(self):
        """Test that importance markers boost ranking"""
        documents = [
            {'content': 'Simple legal text', 'metadata': {'score': 0.5}},
            {'content': 'Text stating that parties shall comply', 'metadata': {'score': 0.5}},
            {'content': 'Penalty must be imposed for violations', 'metadata': {'score': 0.5}}
        ]

        query = "legal requirements"
        ranked = DocumentRanker.rank_documents(documents, query)

        # Documents with "shall" and "must" should rank higher
        self.assertIn('shall', ranked[0]['content'] + ranked[1]['content'])


class TestBangladeshLawRetriever(unittest.TestCase):
    """Test custom retriever for Bangladesh law"""

    @patch('rag.rag_pipeline.VectorSearch')
    def test_retriever_initialization(self, mock_vector_search):
        """Test retriever initialization"""
        retriever = BangladeshLawRetriever(
            vector_search=mock_vector_search,
            top_k=10
        )
        self.assertEqual(retriever.top_k, 10)
        self.assertEqual(retriever.vector_search, mock_vector_search)

    @patch('rag.rag_pipeline.VectorSearch')
    def test_get_relevant_documents(self, mock_vector_search):
        """Test document retrieval"""
        # Mock search results
        mock_results = [
            {
                'content': 'Bangladesh Contract Act provisions',
                'source': 'contract_act.pdf',
                'title': 'Contract Act',
                'year': '2022',
                'score': 0.95,
                'chunk_id': 'chunk_1',
                'language': 'en'
            }
        ]
        mock_vector_search.hybrid_search.return_value = mock_results

        retriever = BangladeshLawRetriever(
            vector_search=mock_vector_search,
            top_k=5
        )

        documents = retriever._get_relevant_documents("contract law query")

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].page_content, 'Bangladesh Contract Act provisions')
        self.assertEqual(documents[0].metadata['title'], 'Contract Act')
        mock_vector_search.hybrid_search.assert_called_once()


class TestRAGPipelineIntegration(unittest.TestCase):
    """Integration tests for RAG pipeline"""

    @patch('rag.rag_pipeline.ChatOpenAI')
    @patch('rag.rag_pipeline.VectorSearch')
    @patch('rag.rag_pipeline.EmbeddingGenerator')
    @patch('rag.rag_pipeline.FaissVectorStore')
    def test_pipeline_initialization(self, mock_faiss, mock_embedding, mock_search, mock_llm):
        """Test pipeline initialization"""
        config = RAGConfig(
            model_name="gpt-4",
            temperature=0.2,
            use_memory=True
        )

        # Mock the components
        mock_embedding.return_value.dimension = 768
        mock_search_instance = MagicMock()
        mock_search.return_value = mock_search_instance

        pipeline = RAGPipeline(config)

        self.assertIsNotNone(pipeline.llm)
        self.assertIsNotNone(pipeline.vector_search)
        self.assertEqual(pipeline.config.temperature, 0.2)

    @patch('rag.rag_pipeline.ChatOpenAI')
    @patch('rag.rag_pipeline.VectorSearch')
    @patch('rag.rag_pipeline.EmbeddingGenerator')
    @patch('rag.rag_pipeline.FaissVectorStore')
    def test_search_similar_laws(self, mock_faiss, mock_embedding, mock_search, mock_llm):
        """Test searching for similar laws"""
        # Setup mocks
        mock_embedding.return_value.dimension = 768
        mock_search_instance = MagicMock()
        mock_search.return_value = mock_search_instance

        mock_results = [
            {'content': 'Law 1', 'score': 0.9},
            {'content': 'Law 2', 'score': 0.8}
        ]
        mock_search_instance.hybrid_search.return_value = mock_results

        pipeline = RAGPipeline()
        results = pipeline.search_similar_laws("property dispute", top_k=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['content'], 'Law 1')
        mock_search_instance.hybrid_search.assert_called_once()

    @patch('rag.rag_pipeline.ChatOpenAI')
    @patch('rag.rag_pipeline.VectorSearch')
    @patch('rag.rag_pipeline.EmbeddingGenerator')
    @patch('rag.rag_pipeline.FaissVectorStore')
    def test_memory_management(self, mock_faiss, mock_embedding, mock_search, mock_llm):
        """Test conversation memory management"""
        # Setup mocks
        mock_embedding.return_value.dimension = 768
        mock_search_instance = MagicMock()
        mock_search.return_value = mock_search_instance

        config = RAGConfig(use_memory=True)
        pipeline = RAGPipeline(config)

        # Test memory initialization
        self.assertIsNotNone(pipeline.memory)

        # Test clear memory
        pipeline.clear_memory()
        history = pipeline.get_memory_history()
        self.assertEqual(len(history), 0)

    @patch('rag.rag_pipeline.ChatOpenAI')
    @patch('rag.rag_pipeline.VectorSearch')
    @patch('rag.rag_pipeline.EmbeddingGenerator')
    @patch('rag.rag_pipeline.FaissVectorStore')
    def test_config_update(self, mock_faiss, mock_embedding, mock_search, mock_llm):
        """Test configuration update"""
        # Setup mocks
        mock_embedding.return_value.dimension = 768
        mock_search_instance = MagicMock()
        mock_search.return_value = mock_search_instance

        pipeline = RAGPipeline()
        original_temp = pipeline.config.temperature

        # Update configuration
        pipeline.update_config(temperature=0.5, top_k=10)

        self.assertEqual(pipeline.config.temperature, 0.5)
        self.assertEqual(pipeline.config.top_k, 10)
        self.assertNotEqual(pipeline.config.temperature, original_temp)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestRAGConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestPromptSelector))
    suite.addTests(loader.loadTestsFromTestCase(TestContextWindowManager))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentRanker))
    suite.addTests(loader.loadTestsFromTestCase(TestBangladeshLawRetriever))
    suite.addTests(loader.loadTestsFromTestCase(TestRAGPipelineIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("RAG PIPELINE TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print("\nFailed Tests:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)