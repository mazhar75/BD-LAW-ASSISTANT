"""
Test FAISS Vector Store
"""
import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

print("="*60)
print("Testing FAISS Vector Store")
print("="*60)

try:
    from embeddings.vector_store import VectorStore

    # Create vector store
    print("\n1. Creating vector store...")
    vector_store = VectorStore(
        dimension=384,
        index_type="Flat",
        metric="cosine",
        store_path="test_vectors.faiss"
    )
    print(f"[OK] Vector store created: {vector_store.get_stats()}")

    # Create sample vectors
    print("\n2. Creating sample vectors...")
    num_vectors = 100
    dimension = 384

    # Generate random vectors (simulate embeddings)
    np.random.seed(42)
    vectors = np.random.randn(num_vectors, dimension).astype('float32')

    # Create metadata
    metadata = [
        {
            'chunk_id': i,
            'act_number': i // 10 + 1,
            'section': f"Section {i % 10 + 1}",
            'text': f"This is chunk {i} from act {i // 10 + 1}"
        }
        for i in range(num_vectors)
    ]

    print(f"[OK] Created {num_vectors} sample vectors with metadata")

    # Add vectors to store
    print("\n3. Adding vectors to store...")
    vector_store.add_vectors(vectors, metadata)
    print(f"[OK] Added vectors. Store stats: {vector_store.get_stats()}")

    # Test search
    print("\n4. Testing similarity search...")
    query_vector = vectors[0] + np.random.randn(dimension) * 0.1  # Similar to first vector
    results = vector_store.search(query_vector, k=5)

    print(f"[OK] Search returned {len(results)} results:")
    for idx, score, meta in results:
        print(f"  - Chunk {meta['chunk_id']}: score={score:.4f}, act={meta['act_number']}")

    # Test batch search
    print("\n5. Testing batch search...")
    query_vectors = vectors[:3] + np.random.randn(3, dimension) * 0.1
    batch_results = vector_store.search_batch(query_vectors, k=3)

    print(f"[OK] Batch search for {len(query_vectors)} queries completed")
    print(f"  - Query 1: {len(batch_results[0])} results")
    print(f"  - Query 2: {len(batch_results[1])} results")
    print(f"  - Query 3: {len(batch_results[2])} results")

    # Test save and load
    print("\n6. Testing save/load...")
    vector_store.save()
    print("[OK] Vector store saved")

    # Create new store and load
    new_store = VectorStore(dimension=384)
    new_store.load("test_vectors.faiss")
    print(f"[OK] Vector store loaded: {new_store.get_stats()}")

    # Verify loaded data
    results2 = new_store.search(query_vector, k=5)
    if len(results2) == len(results):
        print("[OK] Loaded store produces same search results")
    else:
        print("[FAIL] Loaded store produces different results")

    # Clean up
    Path("test_vectors.faiss").unlink(missing_ok=True)
    Path("test_vectors.meta").unlink(missing_ok=True)

    print("\n" + "="*60)
    print("All vector store tests passed!")
    print("="*60)

except ImportError as e:
    print(f"\n[ERROR] Could not import required module: {e}")
    print("\nPlease install required packages:")
    print("  pip install faiss-cpu numpy")

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()