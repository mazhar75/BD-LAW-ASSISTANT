"""
Test FastAPI RAG Service
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

print("="*60)
print("Testing FastAPI RAG Service")
print("="*60)

try:
    # Test imports
    print("\n1. Testing module imports...")
    from api import create_app
    from api.config import Settings
    print("[OK] API modules imported successfully")

    # Test app creation
    print("\n2. Creating FastAPI app...")
    app = create_app()
    print(f"[OK] App created: {app.title}")
    print(f"     Version: {app.version}")

    # Check routes
    print("\n3. Checking registered routes...")
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append(f"{list(route.methods)[0] if route.methods else 'GET'} {route.path}")

    print(f"[OK] Found {len(routes)} routes:")
    for route in routes[:10]:  # Show first 10
        print(f"     - {route}")

    # Test configuration
    print("\n4. Testing configuration...")
    settings = Settings()
    print(f"[OK] Configuration loaded:")
    print(f"     Database: {settings.db_name}@{settings.db_host}:{settings.db_port}")
    print(f"     Redis: {settings.redis_host}:{settings.redis_port}")
    print(f"     Embedding model: {settings.embedding_model.split('/')[-1]}")
    print(f"     Vector dimension: {settings.embedding_dimension}")

    # Test Pydantic models
    print("\n5. Testing request/response models...")
    from api.routes.search import SearchRequest, SearchResponse
    from api.routes.query import QueryRequest, QueryResponse

    # Test search request
    search_req = SearchRequest(
        query="What are fundamental rights?",
        language="en",
        top_k=5
    )
    print(f"[OK] SearchRequest created: query='{search_req.query[:30]}...'")

    # Test query request
    query_req = QueryRequest(
        query="Explain property law",
        query_type="question",
        language="en"
    )
    print(f"[OK] QueryRequest created: query='{query_req.query}'")

    print("\n" + "="*60)
    print("FastAPI service test completed successfully!")
    print("="*60)
    print("\nTo run the service:")
    print("  cd services/rag")
    print("  python main.py")
    print("\nThen access:")
    print("  - API docs: http://localhost:8000/docs")
    print("  - Health check: http://localhost:8000/health")
    print("="*60)

except ImportError as e:
    print(f"\n[ERROR] Import failed: {e}")
    print("\nPlease install required packages:")
    print("  pip install fastapi uvicorn pydantic")

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()