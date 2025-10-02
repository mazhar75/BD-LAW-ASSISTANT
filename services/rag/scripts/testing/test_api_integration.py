"""
Integration tests for RAG API endpoints
Tests all query endpoints without requiring external dependencies
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import unittest
import json
from fastapi.testclient import TestClient
from datetime import datetime

from api.app import create_app
from api.schemas import (
    SearchRequest, QuestionRequest, SimilarLawsRequest, FeedbackRequest,
    SearchType, LanguageEnum, FeedbackType
)


class TestAPIIntegration(unittest.TestCase):
    """Integration tests for API endpoints"""

    @classmethod
    def setUpClass(cls):
        """Set up test client"""
        cls.app = create_app()
        cls.client = TestClient(cls.app)

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["service"], "BD Law Assistant RAG Service")
        self.assertEqual(data["version"], "1.0.0")
        self.assertIn("endpoints", data)

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("status", data)


class TestSearchEndpoint(unittest.TestCase):
    """Test search endpoint"""

    @classmethod
    def setUpClass(cls):
        """Set up test client"""
        cls.app = create_app()
        cls.client = TestClient(cls.app)

    def test_search_basic(self):
        """Test basic search functionality"""
        request_data = {
            "query": "property transfer law",
            "top_k": 5,
            "search_type": "hybrid",
            "language": "en"
        }

        response = self.client.post("/api/v1/query/api/v1/search", json=request_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["query"], "property transfer law")
        self.assertIn("results", data)
        self.assertIn("total_results", data)
        self.assertIn("processing_time_ms", data)

    def test_search_with_filters(self):
        """Test search with filters"""
        request_data = {
            "query": "criminal law",
            "top_k": 3,
            "search_type": "semantic",
            "filters": {
                "year": 1860,
                "category": "criminal"
            },
            "language": "en"
        }

        response = self.client.post("/api/v1/query/api/v1/search", json=request_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data["results"], list)
        self.assertLessEqual(len(data["results"]), 3)

    def test_search_invalid_request(self):
        """Test search with invalid request"""
        request_data = {
            "query": "",  # Empty query
            "top_k": 5
        }

        response = self.client.post("/api/v1/query/api/v1/search", json=request_data)
        self.assertEqual(response.status_code, 422)  # Validation error

    def test_search_bengali_language(self):
        """Test search with Bengali language preference"""
        request_data = {
            "query": "সম্পত্তি হস্তান্তর আইন",
            "top_k": 5,
            "search_type": "hybrid",
            "language": "bn"
        }

        response = self.client.post("/api/v1/query/api/v1/search", json=request_data)
        self.assertEqual(response.status_code, 200)


class TestQuestionAnswerEndpoint(unittest.TestCase):
    """Test Q&A endpoint"""

    @classmethod
    def setUpClass(cls):
        """Set up test client"""
        cls.app = create_app()
        cls.client = TestClient(cls.app)
        cls.session_id = None

    def test_ask_question_basic(self):
        """Test basic question answering"""
        request_data = {
            "question": "What are the requirements for property transfer in Bangladesh?",
            "use_chat_history": False,
            "language": "en",
            "include_sources": True,
            "max_tokens": 500
        }

        response = self.client.post("/api/v1/query/api/v1/ask", json=request_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["question"], request_data["question"])
        self.assertIn("answer", data)
        self.assertIn("query_id", data)
        self.assertIn("session_id", data)
        self.assertIn("confidence_score", data)
        self.assertIn("tokens_used", data)

        # Store session ID for next test
        self.__class__.session_id = data["session_id"]

    def test_ask_with_session(self):
        """Test question with session history"""
        if not self.session_id:
            self.skipTest("No session ID available")

        request_data = {
            "question": "What about commercial properties?",
            "use_chat_history": True,
            "session_id": self.session_id,
            "language": "en",
            "include_sources": True,
            "max_tokens": 500
        }

        response = self.client.post("/api/v1/query/api/v1/ask", json=request_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["session_id"], self.session_id)

    def test_ask_without_sources(self):
        """Test question without source documents"""
        request_data = {
            "question": "Explain contract law",
            "include_sources": False,
            "max_tokens": 200
        }

        response = self.client.post("/api/v1/query/api/v1/ask", json=request_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsNone(data.get("source_documents"))

    def test_ask_with_large_token_limit(self):
        """Test question with large token limit"""
        request_data = {
            "question": "Provide a comprehensive overview of Bangladesh criminal law",
            "max_tokens": 4096
        }

        response = self.client.post("/api/v1/query/api/v1/ask", json=request_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("tokens_used", data)


class TestSimilarLawsEndpoint(unittest.TestCase):
    """Test similar laws endpoint"""

    @classmethod
    def setUpClass(cls):
        """Set up test client"""
        cls.app = create_app()
        cls.client = TestClient(cls.app)

    def test_find_similar_laws(self):
        """Test finding similar laws"""
        request_data = {
            "reference_text": "Section 302 of the Penal Code deals with punishment for murder",
            "top_k": 5
        }

        response = self.client.post("/api/v1/query/api/v1/similar", json=request_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("reference_text", data)
        self.assertIn("similar_laws", data)
        self.assertIn("total_found", data)
        self.assertIn("processing_time_ms", data)

        # Check similar laws structure
        if data["similar_laws"]:
            similar_law = data["similar_laws"][0]
            self.assertIn("content", similar_law)
            self.assertIn("metadata", similar_law)
            self.assertIn("similarity_score", similar_law)
            self.assertIn("key_similarities", similar_law)

    def test_find_similar_with_filters(self):
        """Test finding similar laws with filters"""
        request_data = {
            "reference_text": "Property ownership and transfer regulations",
            "top_k": 3,
            "filters": {
                "category": "civil"
            }
        }

        response = self.client.post("/api/v1/query/api/v1/similar", json=request_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertLessEqual(len(data["similar_laws"]), 3)


class TestFeedbackEndpoint(unittest.TestCase):
    """Test feedback endpoint"""

    @classmethod
    def setUpClass(cls):
        """Set up test client"""
        cls.app = create_app()
        cls.client = TestClient(cls.app)

    def test_submit_positive_feedback(self):
        """Test submitting positive feedback"""
        request_data = {
            "query_id": "q-test-123",
            "feedback_type": "positive",
            "rating": 5,
            "comment": "Very helpful response"
        }

        response = self.client.post("/api/v1/query/api/v1/feedback", json=request_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("feedback_id", data)
        self.assertEqual(data["status"], "success")
        self.assertIn("message", data)

    def test_submit_negative_feedback(self):
        """Test submitting negative feedback"""
        request_data = {
            "query_id": "q-test-456",
            "feedback_type": "negative",
            "rating": 2,
            "comment": "Answer was not relevant"
        }

        response = self.client.post("/api/v1/query/api/v1/feedback", json=request_data)
        self.assertEqual(response.status_code, 200)

    def test_submit_correction_feedback(self):
        """Test submitting correction feedback"""
        request_data = {
            "query_id": "q-test-789",
            "feedback_type": "correction",
            "rating": 3,
            "comment": "The correct answer should be...",
            "correct_answer": "The correct interpretation of Section 420 is..."
        }

        response = self.client.post("/api/v1/query/api/v1/feedback", json=request_data)
        self.assertEqual(response.status_code, 200)

    def test_feedback_invalid_rating(self):
        """Test feedback with invalid rating"""
        request_data = {
            "query_id": "q-test-999",
            "feedback_type": "positive",
            "rating": 10  # Invalid: should be 1-5
        }

        response = self.client.post("/api/v1/query/api/v1/feedback", json=request_data)
        self.assertEqual(response.status_code, 422)  # Validation error


class TestSessionManagement(unittest.TestCase):
    """Test session management endpoints"""

    @classmethod
    def setUpClass(cls):
        """Set up test client"""
        cls.app = create_app()
        cls.client = TestClient(cls.app)
        cls.session_id = None

    def test_create_session_via_question(self):
        """Test session creation through question"""
        request_data = {
            "question": "What is property law?",
            "use_chat_history": True
        }

        response = self.client.post("/api/v1/query/api/v1/ask", json=request_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("session_id", data)
        self.__class__.session_id = data["session_id"]

    def test_get_session_history(self):
        """Test getting session history"""
        if not self.session_id:
            self.skipTest("No session ID available")

        response = self.client.get(f"/api/v1/query/session/{self.session_id}/history")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["session_id"], self.session_id)
        self.assertIn("session_data", data)
        self.assertIn("conversation_history", data)

    def test_clear_session(self):
        """Test clearing session"""
        if not self.session_id:
            self.skipTest("No session ID available")

        response = self.client.delete(f"/api/v1/query/session/{self.session_id}")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "success")

        # Verify session is cleared
        response = self.client.get(f"/api/v1/query/session/{self.session_id}/history")
        self.assertEqual(response.status_code, 404)

    def test_get_nonexistent_session(self):
        """Test getting non-existent session"""
        response = self.client.get("/api/v1/query/session/nonexistent-session/history")
        self.assertEqual(response.status_code, 404)


class TestErrorHandling(unittest.TestCase):
    """Test error handling across endpoints"""

    @classmethod
    def setUpClass(cls):
        """Set up test client"""
        cls.app = create_app()
        cls.client = TestClient(cls.app)

    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        response = self.client.post(
            "/api/v1/query/api/v1/search",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 422)

    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        # Missing 'question' field
        response = self.client.post("/api/v1/query/api/v1/ask", json={})
        self.assertEqual(response.status_code, 422)

    def test_invalid_enum_values(self):
        """Test handling of invalid enum values"""
        request_data = {
            "query": "test query",
            "search_type": "invalid_type"  # Invalid enum value
        }
        response = self.client.post("/api/v1/query/api/v1/search", json=request_data)
        self.assertEqual(response.status_code, 422)


def run_tests():
    """Run all API integration tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestAPIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchEndpoint))
    suite.addTests(loader.loadTestsFromTestCase(TestQuestionAnswerEndpoint))
    suite.addTests(loader.loadTestsFromTestCase(TestSimilarLawsEndpoint))
    suite.addTests(loader.loadTestsFromTestCase(TestFeedbackEndpoint))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("API INTEGRATION TEST SUMMARY")
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

    print("\nAPI Endpoints Tested:")
    print("  ✓ GET  /")
    print("  ✓ GET  /health")
    print("  ✓ POST /api/v1/search")
    print("  ✓ POST /api/v1/ask")
    print("  ✓ POST /api/v1/similar")
    print("  ✓ POST /api/v1/feedback")
    print("  ✓ GET  /api/v1/session/{id}/history")
    print("  ✓ DELETE /api/v1/session/{id}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)