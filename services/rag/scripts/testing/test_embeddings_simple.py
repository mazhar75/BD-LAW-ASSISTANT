"""
Simple test for embedding generator (without actual model loading)
"""
import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

print("="*60)
print("Testing Embedding Generator Setup")
print("="*60)

# Test 1: Check if modules can be imported
try:
    print("\n1. Checking module imports...")
    from embeddings.embedding_generator import EmbeddingGenerator, SENTENCE_TRANSFORMERS_AVAILABLE

    if SENTENCE_TRANSFORMERS_AVAILABLE:
        print("[OK] sentence-transformers is installed")
    else:
        print("[INFO] sentence-transformers not yet installed")
        print("      Install with: pip install sentence-transformers")

    # Check available models
    print("\n2. Available pre-configured models:")
    models = EmbeddingGenerator.list_available_models()
    for name, model_path in models.items():
        print(f"   - {name}: {model_path}")

    print("\n3. Module structure verified successfully")

except ImportError as e:
    print(f"[ERROR] Import failed: {e}")

# Test 2: Check integration with vector store
try:
    print("\n4. Testing vector store integration...")
    from embeddings import VectorStore

    # Create mock embeddings
    dimension = 384
    num_texts = 5
    mock_embeddings = np.random.randn(num_texts, dimension).astype('float32')

    # Create vector store
    store = VectorStore(dimension=dimension)

    # Add mock embeddings
    metadata = [{"text_id": i, "content": f"Text {i}"} for i in range(num_texts)]
    store.add_vectors(mock_embeddings, metadata)

    # Test search
    query = mock_embeddings[0] + np.random.randn(dimension) * 0.1
    results = store.search(query, k=3)

    print(f"[OK] Vector store integration working")
    print(f"     Added {num_texts} vectors, search returned {len(results)} results")

except Exception as e:
    print(f"[ERROR] Vector store test failed: {e}")

print("\n" + "="*60)
print("Setup verification complete!")
print("="*60)
print("\nNext steps:")
print("1. Wait for sentence-transformers installation to complete")
print("2. Run full test: python test_embeddings.py")
print("3. The system will download models on first use (~400MB)")
print("="*60)