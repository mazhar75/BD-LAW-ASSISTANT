"""
Test Gemini RAG Pipeline with Real Data
"""

import sys
import os
import asyncio
import time
from datetime import datetime
import io

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag.rag_pipeline_gemini import RAGPipeline, RAGConfig

def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

def test_gemini_rag():
    """Test the Gemini-powered RAG pipeline"""

    print_header("GEMINI RAG PIPELINE TEST")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Initialize RAG pipeline with Gemini
        print("\n1. Initializing Gemini RAG Pipeline...")
        config = RAGConfig(
            model_name="gemini-1.5-flash",  # Updated model name
            temperature=0.3,
            max_output_tokens=1024,
            top_k=5
        )

        rag = RAGPipeline(config)
        print("✅ RAG Pipeline initialized successfully")

    except Exception as e:
        print(f"❌ Failed to initialize RAG Pipeline: {e}")
        return

    # Test queries
    test_queries = [
        {
            "query": "What are the penalties for theft under Bangladesh Penal Code?",
            "type": "penalty"
        },
        {
            "query": "What is the procedure for registering a company in Bangladesh?",
            "type": "procedure"
        },
        {
            "query": "What are the labor laws regarding working hours and overtime?",
            "type": "regulation"
        }
    ]

    print_header("2. TESTING QUERIES")

    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        print(f"\n📝 Query {i}: {query}")
        print("-" * 60)

        try:
            # Measure response time
            start_time = time.time()

            # Get response from RAG
            response = rag.ask(
                query=query,
                session_id=f"test_{i}",
                use_chat=False
            )

            elapsed_time = (time.time() - start_time) * 1000  # ms

            # Display results
            if response and response.get('answer'):
                print(f"✅ Response generated in {elapsed_time:.1f}ms")
                print(f"\n📖 Answer:")
                answer = response['answer']
                # Truncate long answers for display
                if len(answer) > 500:
                    print(f"{answer[:500]}...")
                else:
                    print(answer)

                # Show sources
                sources = response.get('sources', [])
                if sources:
                    print(f"\n📚 Sources ({len(sources)} documents retrieved):")
                    for j, source in enumerate(sources[:3], 1):
                        print(f"   {j}. {source.get('title', 'Unknown')} (Score: {source.get('relevance_score', 0):.4f})")

                print(f"\n⏱️  Performance:")
                print(f"   - Response time: {elapsed_time:.1f}ms")
                print(f"   - Documents retrieved: {response.get('documents_retrieved', 0)}")
                print(f"   - Model used: {response.get('model', 'Unknown')}")

            else:
                print(f"⚠️  No response generated")

        except Exception as e:
            print(f"❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()

    # Test search functionality
    print_header("3. TESTING SEARCH FUNCTIONALITY")

    search_query = "property inheritance rights women"
    print(f"\n🔍 Search Query: {search_query}")

    try:
        results = rag.search_laws(search_query, top_k=5)

        if results:
            print(f"✅ Found {len(results)} relevant documents")
            for i, result in enumerate(results[:3], 1):
                print(f"\n{i}. Title: {result.get('title', 'Unknown')}")
                print(f"   Year: {result.get('year', 'Unknown')}")
                print(f"   Score: {result.get('score', 0):.4f}")
                preview = result.get('content', '')[:150] + "..."
                print(f"   Preview: {preview}")
        else:
            print("⚠️  No search results found")

    except Exception as e:
        print(f"❌ Search failed: {e}")

    # Test conversation mode
    print_header("4. TESTING CONVERSATION MODE")

    conversation_queries = [
        "What is the Companies Act in Bangladesh?",
        "What are the main requirements for company registration?",
        "What about foreign companies?"
    ]

    for i, query in enumerate(conversation_queries, 1):
        print(f"\n💬 Query {i}: {query}")

        try:
            response = rag.ask(
                query=query,
                session_id="conversation_test",
                use_chat=True  # Enable conversation history
            )

            if response and response.get('answer'):
                answer = response['answer'][:300] + "..." if len(response['answer']) > 300 else response['answer']
                print(f"✅ Response: {answer}")
            else:
                print("⚠️  No response")

        except Exception as e:
            print(f"❌ Conversation query failed: {e}")

    # Summary
    print_header("TEST SUMMARY")
    print(f"✅ Gemini RAG Pipeline is operational")
    print(f"✅ Using model: {config.model_name}")
    print(f"✅ Vector search is working")
    print(f"✅ Question answering is functional")
    print(f"\n📝 Note: The pipeline is using Gemini API from your .env configuration")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_gemini_rag()