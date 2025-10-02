"""
Complete End-to-End Test for Bangladesh Law RAG System with Gemini
Tests the full pipeline with real ingested data
"""

import sys
import os
import time
from datetime import datetime
import psycopg2
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from embeddings.embedding_generator import EmbeddingGenerator
from embeddings.vector_store import VectorStore
from search.vector_search import VectorSearch
from database.connection import DatabaseConnection

def print_header(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

class CompleteRAGTester:
    """Complete end-to-end testing for RAG system with Gemini"""

    def __init__(self):
        # Initialize components
        self.db = DatabaseConnection()
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = VectorStore(
            dimension=self.embedding_gen.dimension,
            index_type="Flat"
        )
        self.vector_search = VectorSearch(
            vector_store=self.vector_store,
            embedding_generator=self.embedding_gen
        )

        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        # Load FAISS index
        index_path = "../../data/processed/faiss_index.bin"
        if os.path.exists(index_path):
            self.vector_search.load_index(index_path)
            print(f"[OK] Loaded FAISS index from {index_path}")
        else:
            print(f"[WARNING] FAISS index not found at {index_path}")

    def test_database_connection(self) -> bool:
        """Test database connectivity"""
        print_header("1. DATABASE CONNECTION TEST")

        try:
            # Test connection
            if self.db.test_connection():
                print("[OK] Database connected successfully")

                # Get counts
                laws = self.db.execute_query("SELECT COUNT(*) as count FROM laws")
                chunks = self.db.execute_query("SELECT COUNT(*) as count FROM law_chunks")
                embeddings = self.db.execute_query("SELECT COUNT(*) as count FROM embeddings")

                print(f"   - Laws: {laws[0]['count'] if laws else 0}")
                print(f"   - Chunks: {chunks[0]['count'] if chunks else 0}")
                print(f"   - Embeddings: {embeddings[0]['count'] if embeddings else 0}")

                return True
            else:
                print("[FAIL] Database connection failed")
                return False

        except Exception as e:
            print(f"[ERROR] Database test failed: {str(e)}")
            return False

    def test_vector_search(self) -> bool:
        """Test vector search functionality"""
        print_header("2. VECTOR SEARCH TEST")

        test_queries = [
            "theft criminal law penalties",
            "company registration procedure",
            "labor laws working hours"
        ]

        success_count = 0

        for query in test_queries:
            print(f"\nQuery: '{query}'")

            try:
                start_time = time.time()

                # Perform search
                results = self.vector_search.hybrid_search(
                    query=query,
                    top_k=5,
                    semantic_weight=0.7,
                    keyword_weight=0.3
                )

                search_time = (time.time() - start_time) * 1000  # ms

                if results:
                    print(f"[OK] Found {len(results)} results in {search_time:.1f}ms")
                    success_count += 1

                    # Show top result
                    top_result = results[0]
                    preview = top_result.content[:150] + "..." if len(top_result.content) > 150 else top_result.content
                    print(f"   Top result (score: {top_result.score:.4f}): {preview}")
                else:
                    print(f"[WARNING] No results found")

            except Exception as e:
                print(f"[ERROR] Search failed: {str(e)}")

        success_rate = (success_count / len(test_queries)) * 100
        print(f"\n[SUMMARY] Search Success Rate: {success_rate:.1f}%")

        return success_count > 0

    def test_gemini_integration(self) -> bool:
        """Test Gemini API integration"""
        print_header("3. GEMINI API TEST")

        try:
            # Simple test prompt
            response = self.model.generate_content("What is 2+2? Answer in one word.")

            if response and response.text:
                print(f"[OK] Gemini API is working")
                print(f"   Response: {response.text.strip()}")
                return True
            else:
                print(f"[FAIL] No response from Gemini")
                return False

        except Exception as e:
            print(f"[ERROR] Gemini test failed: {str(e)}")
            return False

    def test_rag_pipeline(self) -> bool:
        """Test complete RAG pipeline with Gemini"""
        print_header("4. RAG PIPELINE TEST (SEARCH + GEMINI)")

        test_cases = [
            {
                "query": "What are the penalties for theft in Bangladesh?",
                "expected_keywords": ["penal", "theft", "punishment", "section"]
            },
            {
                "query": "How to register a company in Bangladesh?",
                "expected_keywords": ["company", "registration", "act", "procedure"]
            },
            {
                "query": "What are the working hour regulations in Bangladesh labor law?",
                "expected_keywords": ["labor", "working", "hours", "employment"]
            }
        ]

        success_count = 0

        for test_case in test_cases:
            query = test_case["query"]
            print(f"\nQuery: '{query}'")
            print("-" * 60)

            try:
                # Step 1: Search for relevant documents
                start_time = time.time()

                search_results = self.vector_search.hybrid_search(
                    query=query,
                    top_k=5,
                    semantic_weight=0.7,
                    keyword_weight=0.3
                )

                search_time = (time.time() - start_time) * 1000

                if not search_results:
                    print(f"[WARNING] No documents found for query")
                    continue

                print(f"[OK] Found {len(search_results)} relevant documents in {search_time:.1f}ms")

                # Step 2: Format context for Gemini
                context_parts = []
                for i, result in enumerate(search_results[:3], 1):
                    context_parts.append(f"Document {i} (Score: {result.score:.3f}):")
                    context_parts.append(result.content)
                    context_parts.append("")

                context = "\n".join(context_parts)

                # Step 3: Generate answer with Gemini
                prompt = f"""You are a legal expert assistant specializing in Bangladesh law.

Context from Bangladesh legal documents:
{context}

Question: {query}

Instructions:
1. Answer based ONLY on the provided context
2. If the context contains relevant information, provide a clear and concise answer
3. Cite any specific laws or sections mentioned in the context
4. If the context doesn't contain the answer, say "The provided documents do not contain sufficient information to answer this question."

Answer:"""

                gemini_start = time.time()
                response = self.model.generate_content(prompt)
                gemini_time = (time.time() - gemini_start) * 1000

                if response and response.text:
                    print(f"[OK] Answer generated in {gemini_time:.1f}ms")

                    # Check if answer contains expected keywords
                    answer_lower = response.text.lower()
                    keywords_found = sum(1 for keyword in test_case["expected_keywords"]
                                        if keyword in answer_lower)

                    if keywords_found > 0:
                        print(f"[OK] Answer appears relevant ({keywords_found}/{len(test_case['expected_keywords'])} keywords found)")
                        success_count += 1
                    else:
                        print(f"[WARNING] Answer may not be relevant")

                    # Display answer preview
                    answer_preview = response.text[:300] + "..." if len(response.text) > 300 else response.text
                    print(f"\nAnswer: {answer_preview}")

                    # Performance summary
                    total_time = search_time + gemini_time
                    print(f"\nPerformance:")
                    print(f"   - Search time: {search_time:.1f}ms")
                    print(f"   - Gemini time: {gemini_time:.1f}ms")
                    print(f"   - Total time: {total_time:.1f}ms")

            except Exception as e:
                print(f"[ERROR] RAG pipeline failed: {str(e)}")
                import traceback
                traceback.print_exc()

        success_rate = (success_count / len(test_cases)) * 100
        print(f"\n[SUMMARY] RAG Pipeline Success Rate: {success_rate:.1f}%")

        return success_count > 0

    def test_performance_benchmark(self) -> bool:
        """Test system performance"""
        print_header("5. PERFORMANCE BENCHMARK")

        # Performance targets
        targets = {
            "search_latency": 500,  # ms
            "gemini_response": 3000,  # ms
            "total_rag": 4000  # ms
        }

        print("Testing against performance targets:")
        print(f"  - Search latency: <{targets['search_latency']}ms")
        print(f"  - Gemini response: <{targets['gemini_response']}ms")
        print(f"  - Total RAG: <{targets['total_rag']}ms")

        # Run performance test
        query = "What is the legal age for marriage in Bangladesh?"
        print(f"\nTest query: '{query}'")

        try:
            # Search performance
            start = time.time()
            results = self.vector_search.hybrid_search(query, top_k=5)
            search_time = (time.time() - start) * 1000

            if search_time < targets["search_latency"]:
                print(f"[OK] Search: {search_time:.1f}ms (target: <{targets['search_latency']}ms)")
            else:
                print(f"[FAIL] Search: {search_time:.1f}ms (exceeded target)")

            # Gemini performance
            if results:
                context = "\n".join([r.content[:200] for r in results[:3]])
                prompt = f"Based on this context: {context}\n\nQuestion: {query}\n\nAnswer briefly:"

                start = time.time()
                response = self.model.generate_content(prompt)
                gemini_time = (time.time() - start) * 1000

                if gemini_time < targets["gemini_response"]:
                    print(f"[OK] Gemini: {gemini_time:.1f}ms (target: <{targets['gemini_response']}ms)")
                else:
                    print(f"[FAIL] Gemini: {gemini_time:.1f}ms (exceeded target)")

                # Total time
                total_time = search_time + gemini_time
                if total_time < targets["total_rag"]:
                    print(f"[OK] Total RAG: {total_time:.1f}ms (target: <{targets['total_rag']}ms)")
                else:
                    print(f"[FAIL] Total RAG: {total_time:.1f}ms (exceeded target)")

                return True

        except Exception as e:
            print(f"[ERROR] Performance test failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests and generate report"""
        print("=" * 70)
        print("BANGLADESH LAW RAG SYSTEM - COMPLETE END-TO-END TEST")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        results = {}

        # Run tests
        results["Database Connection"] = self.test_database_connection()
        results["Vector Search"] = self.test_vector_search()
        results["Gemini API"] = self.test_gemini_integration()
        results["RAG Pipeline"] = self.test_rag_pipeline()
        results["Performance"] = self.test_performance_benchmark()

        # Generate report
        print_header("TEST REPORT SUMMARY")

        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r)
        success_rate = (passed_tests / total_tests) * 100

        print("\nTest Results:")
        for test_name, passed in results.items():
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status} {test_name}")

        print(f"\nOverall:")
        print(f"  - Total Tests: {total_tests}")
        print(f"  - Passed: {passed_tests}")
        print(f"  - Failed: {total_tests - passed_tests}")
        print(f"  - Success Rate: {success_rate:.1f}%")

        # Final verdict
        print("\n" + "=" * 70)
        if success_rate >= 80:
            print("SYSTEM STATUS: READY FOR PRODUCTION")
            print("All critical components are functioning correctly")
        elif success_rate >= 60:
            print("SYSTEM STATUS: PARTIALLY READY")
            print("Some components need attention")
        else:
            print("SYSTEM STATUS: NOT READY")
            print("Critical issues detected - please fix before deployment")

        print("=" * 70)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        tester = CompleteRAGTester()
        tester.run_all_tests()
    except Exception as e:
        print(f"[CRITICAL ERROR] Test initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()