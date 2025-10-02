"""
Test script to verify RAG service setup
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

print("="*60)
print("BD Law Assistant - RAG Service Setup Test")
print("="*60)

# Test 1: Check database module imports
try:
    from database.connection import DatabaseConnection
    from database.models import Law, LawChunk, Embedding, QueryLog
    print("[OK] Database modules imported successfully")
except ImportError as e:
    print(f"[FAIL] Database module import failed: {e}")

# Test 2: Check if PostgreSQL schema file exists
schema_file = Path(__file__).parent / "database" / "schema.sql"
if schema_file.exists():
    print(f"[OK] Schema file exists: {schema_file}")
    with open(schema_file, 'r') as f:
        lines = f.readlines()
        print(f"  - Schema contains {len(lines)} lines")
        tables = [line.strip() for line in lines if line.strip().startswith("CREATE TABLE")]
        print(f"  - Found {len(tables)} CREATE TABLE statements")
else:
    print(f"[FAIL] Schema file not found: {schema_file}")

# Test 3: Test model classes
try:
    law = Law(
        act_number=1,
        title="Test Act",
        full_text="This is a test law",
        year=2024,
        category="Test",
        language="en"
    )
    law_dict = law.to_dict()
    print(f"[OK] Law model created: act_number={law_dict['act_number']}")

    chunk = LawChunk(
        law_id=1,
        chunk_index=0,
        chunk_text="This is a chunk of text",
        section_title="Section 1",
        token_count=5
    )
    chunk_dict = chunk.to_dict()
    print(f"[OK] LawChunk model created: chunk_index={chunk_dict['chunk_index']}")

    embedding = Embedding(
        chunk_id=1,
        model_name="test-model",
        embedding_vector=b"test",
        vector_dimension=384
    )
    emb_dict = embedding.to_dict()
    print(f"[OK] Embedding model created: model={emb_dict['model_name']}")

    query_log = QueryLog(
        query_text="What is the law about?",
        query_language="en",
        response_text="This law is about...",
        model_used="gpt-3.5-turbo"
    )
    query_dict = query_log.to_dict()
    print(f"[OK] QueryLog model created: query={query_dict['query_text'][:20]}...")

except Exception as e:
    print(f"[FAIL] Model test failed: {e}")

# Test 4: Check database connection settings
try:
    from database.connection import DatabaseConnection
    db = DatabaseConnection()
    print("\n" + "="*60)
    print("Database Configuration:")
    print(f"  Host: {db.host}")
    print(f"  Port: {db.port}")
    print(f"  Database: {db.database}")
    print(f"  User: {db.user}")
    print("="*60)

    print("\nNOTE: To test database connection, ensure PostgreSQL is running.")
    print("You can start it with: docker-compose up -d postgres")

except Exception as e:
    print(f"[FAIL] Could not check database config: {e}")

# Test 5: Check required directories
dirs_to_check = [
    Path(__file__).parent / "database",
    Path(__file__).parent / "embeddings",
    Path(__file__).parent / "api",
    Path(__file__).parent / "utils"
]

print("\nChecking directory structure:")
for dir_path in dirs_to_check:
    if dir_path.exists():
        print(f"[OK] {dir_path.name}/ exists")
    else:
        print(f"[FAIL] {dir_path.name}/ not found (will be created)")

print("\n" + "="*60)
print("Setup test completed!")
print("="*60)