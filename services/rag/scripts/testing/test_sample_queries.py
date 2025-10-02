"""
Test sample queries on the RAG system with clean data
"""

from rag.rag_pipeline_gemini import RAGPipeline
from search.vector_search import VectorSearch
import time

def test_sample_queries():
    """Test various legal queries"""

    # Initialize components
    print("Initializing RAG system...")
    pipeline = RAGPipeline()
    search = VectorSearch()

    # Test queries
    queries = [
        "What is theft under Bangladesh law?",
        "Define murder according to criminal law",
        "What constitutes cheating in legal terms?",
        "What are the penalties for forgery?",
        "Explain criminal breach of trust"
    ]

    print("="*70)
    print("SAMPLE QUERY TESTING WITH CLEAN DATA")
    print("="*70)

    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: \"{query}\"")
        print("-"*70)

        try:
            # Search for relevant documents
            start_time = time.time()
            results = search.search(query, top_k=5)
            search_time = (time.time() - start_time) * 1000

            if results:
                print(f"Found {len(results)} relevant documents in {search_time:.1f}ms")

                # Prepare context from search results
                context_docs = []
                for result in results[:3]:  # Use top 3 results
                    context_docs.append({
                        'text': result['text'],
                        'law_id': result.get('law_id', 'Unknown'),
                        'score': result.get('score', 0)
                    })

                # Generate answer using Gemini
                start_time = time.time()

                # Create context string
                context = "\n\n".join([f"Document {j+1}: {doc['text']}"
                                       for j, doc in enumerate(context_docs)])

                # Generate response
                prompt = f"""Based on the following legal documents from Bangladesh law, answer this question: {query}

Context:
{context}

Please provide a clear and concise answer based only on the provided context. If the context doesn't contain enough information, say so."""

                response = pipeline.model.generate_content(prompt)
                answer = response.text
                gen_time = (time.time() - start_time) * 1000

                # Display results
                print(f"\nAnswer:")
                print(answer[:600] + "..." if len(answer) > 600 else answer)

                print(f"\nPerformance:")
                print(f"  - Search time: {search_time:.1f}ms")
                print(f"  - Generation time: {gen_time:.1f}ms")
                print(f"  - Total time: {(search_time + gen_time):.1f}ms")

                print(f"\nTop Sources:")
                for j, doc in enumerate(context_docs, 1):
                    print(f"  {j}. Law ID: {doc['law_id']}")
                    print(f"     Relevance: {doc['score']:.3f}")
                    preview = doc['text'][:100] + "..." if len(doc['text']) > 100 else doc['text']
                    print(f"     Preview: {preview}")

            else:
                print("No relevant documents found")

        except Exception as e:
            print(f"Error: {str(e)}")

    print("\n" + "="*70)
    print("TEST COMPLETED")
    print("="*70)

if __name__ == "__main__":
    test_sample_queries()