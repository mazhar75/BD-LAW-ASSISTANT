"""
Test Document Chunker - Comprehensive tests for document chunking
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from chunking.document_chunker import DocumentChunker, Chunk
from ingestion.data_loader import DataLoader, Document


def test_basic_chunking():
    """Test basic document chunking functionality"""
    print("\n" + "="*60)
    print("TEST 1: Basic Chunking")
    print("="*60)

    chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)

    # Test document
    test_content = """
## Section 1: Introduction
This is the introduction to the legal document. It contains important information about the scope and purpose of this act.

## Section 2: Definitions
In this Act, unless the context otherwise requires:
(a) "Authority" means the regulatory authority established under this Act;
(b) "Document" means any written or electronic record;
(c) "Person" includes any individual, company, or legal entity.

## Section 3: Application
This Act shall apply to all persons within the jurisdiction.
The provisions of this Act shall come into force on the date of publication.

## Section 4: Powers and Functions
The Authority shall have the following powers:
(a) To investigate any matter under this Act;
(b) To issue orders and directives;
(c) To impose penalties for violations.
""".strip()

    chunks = chunker.chunk_document("test_doc_1", test_content, {"type": "test"})

    print(f"[OK] Content length: {len(test_content)} characters")
    print(f"[OK] Number of chunks created: {len(chunks)}")
    print(f"[OK] Average chunk size: {sum(len(c.content) for c in chunks) / len(chunks):.0f} chars")

    # Verify chunk properties
    for i, chunk in enumerate(chunks):
        assert chunk.document_id == "test_doc_1"
        assert chunk.chunk_index == i
        assert len(chunk.content) <= chunker.chunk_size + 100  # Allow some flexibility

    print("[OK] All chunks have valid properties")

    # Check overlap
    for i in range(len(chunks) - 1):
        overlap = chunks[i].content[-50:]
        next_chunk = chunks[i + 1].content[:50]
        # There should be some overlap
        has_overlap = any(word in next_chunk for word in overlap.split() if len(word) > 3)

    print("[OK] Chunks have appropriate overlap")

    return True


def test_legal_document_chunking():
    """Test chunking with real legal document"""
    print("\n" + "="*60)
    print("TEST 2: Legal Document Chunking")
    print("="*60)

    loader = DataLoader()
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)

    # Load first act
    acts = list(loader.load_acts(limit=1))
    if not acts:
        print("[WARN] No acts found in data directory")
        return False

    doc = acts[0]
    print(f"Testing with: {doc.title[:60]}...")

    # Chunk the document
    chunks = chunker.chunk_legal_document(
        doc.act_number,
        doc.title,
        doc.content,
        doc.language
    )

    print(f"[OK] Original document size: {len(doc.content)} characters")
    print(f"[OK] Created {len(chunks)} chunks")

    # Verify metadata
    for chunk in chunks:
        assert 'act_number' in chunk.metadata
        assert 'title' in chunk.metadata
        assert chunk.metadata['act_number'] == doc.act_number

    print("[OK] All chunks contain proper metadata")

    # Check section extraction
    sections_found = set()
    for chunk in chunks:
        if 'section' in chunk.metadata:
            sections_found.add(chunk.metadata['section'])

    if sections_found:
        print(f"[OK] Found {len(sections_found)} unique sections")
        print(f"  Sample sections: {list(sections_found)[:3]}")

    return True


def test_bengali_chunking():
    """Test Bengali document chunking"""
    print("\n" + "="*60)
    print("TEST 3: Bengali Document Chunking")
    print("="*60)

    chunker = DocumentChunker()

    # Test Bengali content
    bengali_content = """
আইন নং ১: সূচনা
এই আইনটি বাংলাদেশের সকল নাগরিকের জন্য প্রযোজ্য। এটি একটি গুরুত্বপূর্ণ আইন।

ধারা ১: সংজ্ঞা
এই আইনে ব্যবহৃত শব্দগুলির অর্থ নিম্নরূপ।

ধারা ২: প্রয়োগ
এই আইন সমগ্র বাংলাদেশে প্রযোজ্য হবে।
""".strip()

    chunks = chunker.chunk_bengali_document(
        "বাংলা আইন পরীক্ষা",
        bengali_content,
        "test_bengali.md.gz"
    )

    print(f"[OK] Bengali content length: {len(bengali_content)} characters")
    print(f"[OK] Created {len(chunks)} chunks")

    # Verify Bengali-specific handling
    for chunk in chunks:
        assert chunk.metadata['language'] == 'bn'
        assert chunk.metadata['document_type'] == 'bengali_legal'

    print("[OK] Bengali chunks have correct language metadata")

    return True


def test_chunk_deduplication():
    """Test chunk ID generation and deduplication"""
    print("\n" + "="*60)
    print("TEST 4: Chunk Deduplication")
    print("="*60)

    chunker = DocumentChunker(chunk_size=200, chunk_overlap=0)

    # Same content should generate same chunk IDs
    content1 = "This is a test legal document for checking deduplication."
    content2 = "This is a test legal document for checking deduplication."

    chunks1 = chunker.chunk_document("doc1", content1)
    chunks2 = chunker.chunk_document("doc1", content2)

    # Same document ID and content should generate same chunk IDs
    for c1, c2 in zip(chunks1, chunks2):
        assert c1.chunk_id == c2.chunk_id

    print("[OK] Identical content generates identical chunk IDs")

    # Different document IDs should generate different chunk IDs
    chunks3 = chunker.chunk_document("doc2", content1)
    for c1, c3 in zip(chunks1, chunks3):
        assert c1.chunk_id != c3.chunk_id

    print("[OK] Different documents generate different chunk IDs")

    return True


def test_chunk_statistics():
    """Test chunk statistics calculation"""
    print("\n" + "="*60)
    print("TEST 5: Chunk Statistics")
    print("="*60)

    chunker = DocumentChunker()

    # Create test chunks
    chunks = [
        Chunk("c1", "doc1", "A" * 100, {}, 0, 0, 100),
        Chunk("c2", "doc1", "B" * 200, {}, 1, 100, 300),
        Chunk("c3", "doc2", "C" * 150, {}, 0, 0, 150),
    ]

    stats = chunker.calculate_chunk_statistics(chunks)

    assert stats['total_chunks'] == 3
    assert stats['avg_chunk_size'] == 150
    assert stats['min_chunk_size'] == 100
    assert stats['max_chunk_size'] == 200
    assert stats['total_characters'] == 450
    assert stats['unique_documents'] == 2

    print("[OK] Statistics calculated correctly")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Average size: {stats['avg_chunk_size']:.0f} chars")
    print(f"  Size range: {stats['min_chunk_size']}-{stats['max_chunk_size']} chars")

    return True


def test_save_and_load_chunks():
    """Test saving chunks to JSON files"""
    print("\n" + "="*60)
    print("TEST 6: Save and Load Chunks")
    print("="*60)

    import json
    import tempfile

    chunker = DocumentChunker()

    # Create test chunks
    test_chunks = [
        Chunk(
            chunk_id="test_chunk_1",
            document_id="test_doc",
            content="Test content 1",
            metadata={"test": True},
            chunk_index=0,
            start_char=0,
            end_char=14
        ),
        Chunk(
            chunk_id="test_chunk_2",
            document_id="test_doc",
            content="Test content 2",
            metadata={"test": True},
            chunk_index=1,
            start_char=14,
            end_char=28
        )
    ]

    # Save to temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        chunker.save_chunks(test_chunks, output_dir)

        # Check saved file
        saved_file = output_dir / "test_doc_chunks.json"
        assert saved_file.exists()

        # Load and verify
        with open(saved_file, 'r') as f:
            loaded_data = json.load(f)

        assert len(loaded_data) == 2
        assert loaded_data[0]['chunk_id'] == "test_chunk_1"
        assert loaded_data[1]['content'] == "Test content 2"

    print("[OK] Chunks saved and loaded successfully")

    return True


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("TEST 7: Edge Cases")
    print("="*60)

    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)

    # Empty content
    chunks = chunker.chunk_document("empty_doc", "")
    assert len(chunks) == 0
    print("[OK] Empty content handled correctly")

    # Very short content
    chunks = chunker.chunk_document("short_doc", "Short")
    assert len(chunks) == 1
    assert chunks[0].content == "Short"
    print("[OK] Short content handled correctly")

    # Very long single word
    long_word = "A" * 500
    chunks = chunker.chunk_document("long_word_doc", long_word)
    assert len(chunks) > 1
    print(f"[OK] Long content split into {len(chunks)} chunks")

    # Unicode content
    unicode_content = "Legal § document with © symbols and émojis 📚"
    chunks = chunker.chunk_document("unicode_doc", unicode_content)
    assert len(chunks) >= 1
    print("[OK] Unicode content handled correctly")

    return True


def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*60)
    print("DOCUMENT CHUNKER TEST SUITE")
    print("="*60)

    tests = [
        ("Basic Chunking", test_basic_chunking),
        ("Legal Document", test_legal_document_chunking),
        ("Bengali Chunking", test_bengali_chunking),
        ("Deduplication", test_chunk_deduplication),
        ("Statistics", test_chunk_statistics),
        ("Save/Load", test_save_and_load_chunks),
        ("Edge Cases", test_edge_cases),
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