"""
Test Embedding Generator
"""
import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

print("="*60)
print("Testing Embedding Generator")
print("="*60)

try:
    from embeddings import EmbeddingGenerator

    # Sample legal texts in English and Bengali
    sample_texts = [
        "The Constitution of Bangladesh guarantees fundamental rights to all citizens.",
        "Every citizen has the right to freedom of speech and expression.",
        "The Penal Code defines various criminal offenses and their punishments.",
        "Contract law governs agreements between parties.",
        "Property rights are protected under the Transfer of Property Act."
    ]

    sample_bengali = [
        "বাংলাদেশের সংবিধান সকল নাগরিকের মৌলিক অধিকার নিশ্চিত করে।",
        "প্রত্যেক নাগরিকের বাক ও মত প্রকাশের স্বাধীনতার অধিকার রয়েছে।"
    ]

    # Test 1: Initialize generator
    print("\n1. Initializing embedding generator...")
    generator = EmbeddingGenerator(
        model_name='multilingual-mini',  # 384-dim model for faster testing
        device='cpu'  # Use CPU for compatibility
    )
    info = generator.get_model_info()
    print(f"[OK] Model loaded: {info['model_name']}")
    print(f"     Dimension: {info['dimension']}")
    print(f"     Device: {info['device']}")

    # Test 2: Generate single embedding
    print("\n2. Testing single text embedding...")
    text = sample_texts[0]
    embedding = generator.generate(text)
    print(f"[OK] Generated embedding shape: {embedding.shape}")
    print(f"     Embedding vector (first 5): {embedding[0][:5]}")

    # Test 3: Generate batch embeddings
    print("\n3. Testing batch embedding...")
    embeddings = generator.generate(sample_texts[:3])
    print(f"[OK] Generated {embeddings.shape[0]} embeddings")
    print(f"     Shape: {embeddings.shape}")

    # Test 4: Test query embedding
    print("\n4. Testing query embedding...")
    query = "What are the fundamental rights?"
    query_embedding = generator.generate_query_embedding(query)
    print(f"[OK] Query embedding shape: {query_embedding.shape}")

    # Test 5: Test similarity computation
    print("\n5. Testing similarity computation...")
    similarity = generator.compute_similarity(
        sample_texts[0],  # Constitution text
        query
    )
    print(f"[OK] Similarity score: {similarity[0][0]:.4f}")

    # Test 6: Test Bengali text
    print("\n6. Testing Bengali text embedding...")
    bengali_embedding = generator.generate(sample_bengali[0])
    print(f"[OK] Bengali embedding shape: {bengali_embedding.shape}")

    # Test 7: Cross-lingual similarity
    print("\n7. Testing cross-lingual similarity...")
    # Compare English and Bengali texts about constitution
    cross_similarity = generator.compute_similarity(
        sample_texts[0],  # English constitution text
        sample_bengali[0]  # Bengali constitution text
    )
    print(f"[OK] Cross-lingual similarity: {cross_similarity[0][0]:.4f}")

    # Test 8: Benchmark performance
    print("\n8. Benchmarking performance...")
    benchmark = generator.benchmark(sample_texts)
    print(f"[OK] Benchmark results:")
    print(f"     Single encoding: {benchmark['single_encoding_ms']:.2f} ms")
    print(f"     Batch encoding: {benchmark['batch_encoding_ms']:.2f} ms")
    print(f"     Texts per second: {benchmark['texts_per_second']:.2f}")

    # Test 9: Test with vector store integration
    print("\n9. Testing vector store integration...")
    from embeddings import VectorStore

    # Create vector store with same dimension
    vector_store = VectorStore(
        dimension=info['dimension'],
        index_type='Flat',
        metric='cosine'
    )

    # Generate embeddings for all texts
    all_embeddings = generator.generate(sample_texts, normalize=True)

    # Add to vector store
    metadata = [{'text': text, 'id': i} for i, text in enumerate(sample_texts)]
    vector_store.add_vectors(all_embeddings, metadata)

    # Search with query
    query_emb = generator.generate_query_embedding(query, normalize=True)
    results = vector_store.search(query_emb, k=3)

    print(f"[OK] Vector store search results:")
    for idx, score, meta in results:
        print(f"     Score {score:.4f}: {meta['text'][:60]}...")

    print("\n" + "="*60)
    print("All embedding tests passed!")
    print("="*60)

except ImportError as e:
    print(f"\n[ERROR] Could not import required module: {e}")
    print("\nPlease install required packages:")
    print("  pip install sentence-transformers torch")

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()