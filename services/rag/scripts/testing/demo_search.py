"""
Demo search with the clean RAG system
"""

from search.vector_search import VectorSearch
from rag.rag_pipeline_gemini import RAGPipeline
import psycopg2
from dotenv import load_dotenv
import os
import time

def demo_search():
    """Demonstrate the RAG system with sample queries"""

    print("Initializing components...")

    # Initialize search with index loading
    search = VectorSearch()
    search.load_index("../../data/processed/faiss_index.bin")

    # Initialize RAG pipeline
    rag = RAGPipeline()

    # Database connection parameters
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', 5432),
        'database': os.getenv('DB_NAME', 'bdlaw'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD')
    }

    # Test queries
    queries = [
        "What is criminal breach of trust?",
        "Define forgery under Bangladesh law",
        "What are the penalties for theft?"
    ]

    print("\n" + "="*70)
    print("BANGLADESH LAW RAG SYSTEM - DEMO")
    print("="*70)

    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: \"{query}\"")
        print("-"*70)

        try:
            # Perform vector search
            start = time.time()
            search_results = search.search(query, top_k=5)
            search_time = (time.time() - start) * 1000

            if search_results:
                print(f"[OK] Found {len(search_results)} relevant documents in {search_time:.1f}ms")

                # Get law details for top results
                conn = psycopg2.connect(**db_config)
                cursor = conn.cursor()

                # Prepare context
                context_parts = []
                sources = []

                for j, result in enumerate(search_results[:3]):
                    chunk_id = result.chunk_id

                    # Get law details
                    cursor.execute("""
                            SELECT l.title, l.act_number, lc.chunk_text
                            FROM law_chunks lc
                            JOIN laws l ON lc.law_id = l.id
                            WHERE lc.id = %s
                    """, (chunk_id,))

                    row = cursor.fetchone()
                    if row:
                        title, act_number, chunk_text = row
                        context_parts.append(f"[{act_number}] {chunk_text}")
                        sources.append({
                            'title': title,
                            'act': act_number,
                            'score': result.score
                        })

                cursor.close()
                conn.close()

                # Generate answer using Gemini
                if context_parts:
                    context = "\n\n".join(context_parts)

                    prompt = f"""You are a Bangladesh law expert. Based on the following legal documents, answer this question: {query}

Legal Context:
{context}

Provide a clear, accurate answer based only on the provided context. Be specific and cite the relevant act numbers."""

                    start = time.time()
                    response = rag.model.generate_content(prompt)
                    answer = response.text
                    gen_time = (time.time() - start) * 1000

                    # Display results
                    print(f"\nAnswer:")
                    print(answer[:600] + "..." if len(answer) > 600 else answer)

                    print(f"\nPerformance:")
                    print(f"  - Search: {search_time:.1f}ms")
                    print(f"  - Generation: {gen_time:.1f}ms")
                    print(f"  - Total: {(search_time + gen_time):.1f}ms")

                    print(f"\nSources:")
                    for j, source in enumerate(sources, 1):
                        print(f"  {j}. {source['title']}")
                        print(f"     Act: {source['act']}")
                        print(f"     Relevance: {source['score']:.3f}")
            else:
                print("[ERROR] No relevant documents found")

        except Exception as e:
            print(f"[ERROR] {str(e)}")

    print("\n" + "="*70)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("="*70)

if __name__ == "__main__":
    demo_search()