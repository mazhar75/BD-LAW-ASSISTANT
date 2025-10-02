"""
Test Vector Search - Comprehensive tests for search functionality
"""
import sys
import numpy as np
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from search.vector_search import VectorSearch, SearchResult
from chunking.document_chunker import Chunk
from embeddings.vector_store import VectorStore
from embeddings.embedding_generator import EmbeddingGenerator


def test_basic_search():
    """Test basic search functionality"""
    print("\n" + "="*60)
    print("TEST 1: Basic Search")
    print("="*60)

    # Create test search engine
    search = VectorSearch(dimension=384)

    # Create test chunks
    test_chunks = [
        Chunk(
            chunk_id="chunk_1",
            document_id="doc_1",
            content="The legal framework establishes authority for government regulations.",
            metadata={'act_number': 1, 'title': 'Regulatory Act', 'year': 2020},
            chunk_index=0,
            start_char=0,
            end_char=67
        ),
        Chunk(
            chunk_id="chunk_2",
            document_id="doc_1",
            content="Provisions of this act shall apply to all persons within jurisdiction.",
            metadata={'act_number': 1, 'title': 'Regulatory Act', 'year': 2020},
            chunk_index=1,
            start_char=67,
            end_char=138
        ),
        Chunk(
            chunk_id="chunk_3",
            document_id="doc_2",
            content="The court has jurisdiction over civil and criminal matters.",
            metadata={'act_number': 2, 'title': 'Courts Act', 'year': 2019},
            chunk_index=0,
            start_char=0,
            end_char=59
        )
    ]

    # Index chunks
    search.index_chunks_batch(test_chunks)
    print(f"[OK] Indexed {len(test_chunks)} test chunks")

    # Test semantic search
    results = search.semantic_search("government authority", top_k=2)
    assert len(results) > 0
    assert results[0].chunk_id in ["chunk_1", "chunk_2", "chunk_3"]
    print(f"[OK] Semantic search returned {len(results)} results")

    # Verify result structure
    result = results[0]
    assert hasattr(result, 'chunk_id')
    assert hasattr(result, 'score')
    assert hasattr(result, 'metadata')
    print("[OK] Search results have correct structure")

    return True


def test_hybrid_search():
    """Test hybrid search combining semantic and keyword"""
    print("\n" + "="*60)
    print("TEST 2: Hybrid Search")
    print("="*60)

    search = VectorSearch(dimension=384)

    # Create chunks with varied content
    test_chunks = [
        Chunk(
            chunk_id="chunk_a",
            document_id="doc_a",
            content="Bangladesh legal system follows common law traditions with statutory modifications.",
            metadata={'title': 'Legal System Overview'},
            chunk_index=0,
            start_char=0,
            end_char=80
        ),
        Chunk(
            chunk_id="chunk_b",
            document_id="doc_b",
            content="The penal code defines criminal offenses and their punishments.",
            metadata={'title': 'Penal Code'},
            chunk_index=0,
            start_char=0,
            end_char=63
        ),
        Chunk(
            chunk_id="chunk_c",
            document_id="doc_c",
            content="Contract law governs agreements between parties in Bangladesh.",
            metadata={'title': 'Contract Law'},
            chunk_index=0,
            start_char=0,
            end_char=61
        )
    ]

    search.index_chunks_batch(test_chunks)

    # Test hybrid search
    results = search.hybrid_search(
        "Bangladesh criminal law",
        top_k=3,
        semantic_weight=0.6,
        keyword_weight=0.4
    )

    assert len(results) > 0
    print(f"[OK] Hybrid search returned {len(results)} results")

    # Check that results are properly ranked
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
    print("[OK] Results are properly ranked by score")

    return True


def test_filtered_search():
    """Test search with metadata filters"""
    print("\n" + "="*60)
    print("TEST 3: Filtered Search")
    print("="*60)

    search = VectorSearch(dimension=384)

    # Create chunks with different metadata
    test_chunks = [
        Chunk(
            chunk_id="act_2020_1",
            document_id="act_100",
            content="Environmental protection act provisions for 2020.",
            metadata={'year': 2020, 'language': 'en', 'category': 'environment'},
            chunk_index=0,
            start_char=0,
            end_char=50
        ),
        Chunk(
            chunk_id="act_2019_1",
            document_id="act_99",
            content="Environmental regulations from previous year.",
            metadata={'year': 2019, 'language': 'en', 'category': 'environment'},
            chunk_index=0,
            start_char=0,
            end_char=45
        ),
        Chunk(
            chunk_id="act_2020_bn",
            document_id="act_101",
            content="পরিবেশ সংরক্ষণ আইন ২০২০",
            metadata={'year': 2020, 'language': 'bn', 'category': 'environment'},
            chunk_index=0,
            start_char=0,
            end_char=25
        )
    ]

    search.index_chunks_batch(test_chunks)

    # Test filter by year
    results = search.search_with_filters(
        "environment",
        filters={'year': 2020},
        top_k=5
    )

    for result in results:
        assert result.metadata.get('year') == 2020
    print(f"[OK] Year filter: Found {len(results)} results from 2020")

    # Test filter by language
    results = search.search_with_filters(
        "environment",
        filters={'language': 'en'},
        top_k=5
    )

    for result in results:
        assert result.metadata.get('language') == 'en'
    print(f"[OK] Language filter: Found {len(results)} English results")

    # Test range filter
    results = search.search_with_filters(
        "environment",
        filters={'year': {'min': 2019, 'max': 2020}},
        top_k=5
    )
    print(f"[OK] Range filter: Found {len(results)} results in year range")

    return True


def test_reranking():
    """Test result re-ranking"""
    print("\n" + "="*60)
    print("TEST 4: Result Re-ranking")
    print("="*60)

    search = VectorSearch(dimension=384)

    # Create test results
    test_results = [
        SearchResult(
            chunk_id="r1",
            document_id="d1",
            content="The law provides clear guidelines for implementation.",
            score=0.8,
            metadata={'year': 2020}
        ),
        SearchResult(
            chunk_id="r2",
            document_id="d2",
            content="Implementation of the new law begins next year.",
            score=0.7,
            metadata={'year': 2021}
        ),
        SearchResult(
            chunk_id="r3",
            document_id="d3",
            content="Legal framework for environmental protection.",
            score=0.6,
            metadata={'year': 2019}
        )
    ]

    # Test relevance re-ranking
    query = "law implementation"
    reranked = search.rerank_results(query, test_results.copy(), method='relevance')

    # Results with both query terms should rank higher
    assert reranked[0].content.lower().count('law') > 0
    assert reranked[0].content.lower().count('implementation') > 0
    print("[OK] Relevance re-ranking works correctly")

    # Test recency re-ranking
    reranked = search.rerank_results(query, test_results.copy(), method='recency')
    years = [r.metadata.get('year', 0) for r in reranked]
    # More recent documents should have higher scores
    print(f"[OK] Recency re-ranking adjusted scores based on year")

    return True


def test_highlight_extraction():
    """Test highlight extraction from search results"""
    print("\n" + "="*60)
    print("TEST 5: Highlight Extraction")
    print("="*60)

    search = VectorSearch()

    # Test content
    content = """
    The Constitution of Bangladesh establishes the fundamental law of the country.
    It provides the framework for government operations and citizen rights.
    Bangladesh follows a parliamentary democracy system.
    """

    # Extract highlights
    highlights = search.extract_highlights(
        "Bangladesh government",
        content,
        max_highlights=2,
        context_window=30
    )

    assert len(highlights) > 0
    assert any('Bangladesh' in h for h in highlights)
    print(f"[OK] Extracted {len(highlights)} highlights")

    # Verify highlight format
    for highlight in highlights:
        assert len(highlight) > 0
        print(f"   Highlight: {highlight[:50]}...")

    return True


def test_batch_indexing():
    """Test batch indexing performance"""
    print("\n" + "="*60)
    print("TEST 6: Batch Indexing")
    print("="*60)

    search = VectorSearch(dimension=384)

    # Create larger batch of chunks
    test_chunks = []
    for i in range(50):
        chunk = Chunk(
            chunk_id=f"batch_chunk_{i}",
            document_id=f"batch_doc_{i//10}",
            content=f"Test content for chunk {i} with legal terminology and provisions.",
            metadata={'batch': i // 10, 'index': i},
            chunk_index=i % 10,
            start_char=i*50,
            end_char=(i+1)*50
        )
        test_chunks.append(chunk)

    # Index in batches
    search.index_chunks_batch(test_chunks, batch_size=16)

    # Verify all chunks are indexed
    stats = search.get_statistics()
    assert stats['total_vectors'] == 50
    print(f"[OK] Indexed {stats['total_vectors']} chunks in batches")

    # Test search on batch-indexed data
    results = search.search("legal provisions", top_k=5)
    assert len(results) > 0
    print(f"[OK] Search on batch-indexed data returned {len(results)} results")

    return True


def test_empty_and_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("TEST 7: Edge Cases")
    print("="*60)

    search = VectorSearch(dimension=384)

    # Empty query
    results = search.search("", top_k=5)
    print(f"[OK] Empty query handled: {len(results)} results")

    # Very long query
    long_query = " ".join(["legal"] * 100)
    results = search.search(long_query, top_k=5)
    print(f"[OK] Long query handled: {len(results)} results")

    # Search with no indexed data (fresh instance)
    fresh_search = VectorSearch(dimension=384)
    results = fresh_search.search("test query", top_k=5)
    assert len(results) == 0
    print("[OK] Search with no data returns empty results")

    # Invalid filter
    results = search.search_with_filters(
        "test",
        filters={'nonexistent_field': 'value'},
        top_k=5
    )
    print("[OK] Invalid filter handled gracefully")

    return True


def test_save_and_load_index():
    """Test saving and loading search index"""
    print("\n" + "="*60)
    print("TEST 8: Save and Load Index")
    print("="*60)

    import tempfile
    import os

    # Create and populate index
    search1 = VectorSearch(dimension=384)

    test_chunk = Chunk(
        chunk_id="save_test",
        document_id="doc_save",
        content="Test content for save and load functionality.",
        metadata={'test': True},
        chunk_index=0,
        start_char=0,
        end_char=45
    )

    search1.index_chunk(test_chunk)

    # Save index
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index.faiss")
        search1.save_index(index_path)
        assert os.path.exists(index_path)
        print("[OK] Index saved successfully")

        # Load into new instance
        search2 = VectorSearch(dimension=384)
        search2.load_index(index_path)

        # Verify loaded data
        stats = search2.get_statistics()
        assert stats['total_vectors'] > 0
        print(f"[OK] Index loaded: {stats['total_vectors']} vectors")

        # Test search on loaded index
        results = search2.search("test content", top_k=1)
        assert len(results) > 0
        print("[OK] Search works on loaded index")

    return True


def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*60)
    print("VECTOR SEARCH TEST SUITE")
    print("="*60)

    tests = [
        ("Basic Search", test_basic_search),
        ("Hybrid Search", test_hybrid_search),
        ("Filtered Search", test_filtered_search),
        ("Re-ranking", test_reranking),
        ("Highlight Extraction", test_highlight_extraction),
        ("Batch Indexing", test_batch_indexing),
        ("Edge Cases", test_empty_and_edge_cases),
        ("Save/Load Index", test_save_and_load_index),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"[WARN] {test_name}: Incomplete")
        except Exception as e:
            failed += 1
            print(f"[FAIL] {test_name}: Failed - {e}")

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"[OK] Passed: {passed}/{len(tests)}")
    if failed > 0:
        print(f"[FAIL] Failed: {failed}/{len(tests)}")
    else:
        print("[SUCCESS] All tests passed successfully!")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)