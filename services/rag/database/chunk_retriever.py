"""
Chunk retrieval functions for fetching text content from PostgreSQL
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'bdlaw',
    'user': 'postgres',
    'password': 'nihad1086'
}


def get_db_connection():
    """Get a connection to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


def get_chunk_by_db_id(db_id: int) -> Optional[Dict]:
    """
    Retrieve a chunk by its database ID

    Args:
        db_id: The database row ID (e.g., 81952)

    Returns:
        Dictionary with chunk data or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                id as db_id,
                law_id,
                chunk_index,
                chunk_text,
                section_title,
                section_number,
                language
            FROM law_chunks
            WHERE id = %s
        """

        cursor.execute(query, (db_id,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return dict(result)
        return None

    except Exception as e:
        logger.error(f"Error retrieving chunk {db_id}: {e}")
        return None


def get_chunk_by_faiss_index(faiss_index: int) -> Optional[Dict]:
    """
    Retrieve a chunk by FAISS vector index (0-based)
    Maps FAISS index to database ID

    Args:
        faiss_index: The FAISS vector index (0 to 29213)

    Returns:
        Dictionary with chunk data or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Convert numpy int64 to Python int if necessary
        if hasattr(faiss_index, 'item'):
            faiss_index = int(faiss_index.item())
        else:
            faiss_index = int(faiss_index)

        # Get the database ID by offset
        # FAISS indices are 0-based, database IDs start from 81952
        query = """
            SELECT
                id as db_id,
                law_id,
                chunk_index,
                chunk_text,
                section_title,
                section_number,
                language
            FROM law_chunks
            ORDER BY id
            LIMIT 1 OFFSET %s
        """

        cursor.execute(query, (faiss_index,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return dict(result)
        return None

    except Exception as e:
        logger.error(f"Error retrieving chunk at index {faiss_index}: {e}")
        return None


def get_chunks_batch(db_ids: List[int]) -> List[Dict]:
    """
    Batch retrieve multiple chunks by database IDs

    Args:
        db_ids: List of database row IDs

    Returns:
        List of dictionaries with chunk data
    """
    if not db_ids:
        return []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Use IN clause for batch retrieval
        query = """
            SELECT
                id as db_id,
                law_id,
                chunk_index,
                chunk_text,
                section_title,
                section_number,
                language
            FROM law_chunks
            WHERE id IN %s
            ORDER BY id
        """

        cursor.execute(query, (tuple(db_ids),))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return [dict(row) for row in results]

    except Exception as e:
        logger.error(f"Error retrieving batch chunks: {e}")
        return []


def get_chunks_by_faiss_indices(faiss_indices: List[int]) -> List[Dict]:
    """
    Batch retrieve chunks by FAISS indices

    Args:
        faiss_indices: List of FAISS vector indices (0-based)

    Returns:
        List of dictionaries with chunk data
    """
    if not faiss_indices:
        return []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        chunks = []
        for idx in faiss_indices:
            # Convert numpy int64 to Python int if necessary
            if hasattr(idx, 'item'):
                idx = int(idx.item())
            else:
                idx = int(idx)

            query = """
                SELECT
                    id as db_id,
                    law_id,
                    chunk_index,
                    chunk_text,
                    section_title,
                    section_number,
                    language
                FROM law_chunks
                ORDER BY id
                LIMIT 1 OFFSET %s
            """

            cursor.execute(query, (idx,))
            result = cursor.fetchone()
            if result:
                chunks.append(dict(result))

        cursor.close()
        conn.close()

        return chunks

    except Exception as e:
        logger.error(f"Error retrieving chunks by indices: {e}")
        return []


@lru_cache(maxsize=1000)
def get_chunk_cached(faiss_index: int) -> Optional[str]:
    """
    Get chunk text with caching for frequently accessed chunks

    Args:
        faiss_index: The FAISS vector index

    Returns:
        The chunk text or None if not found
    """
    chunk = get_chunk_by_faiss_index(faiss_index)
    return chunk.get('chunk_text') if chunk else None


def get_mapping_offset() -> int:
    """
    Get the offset between FAISS index and database ID
    The first FAISS index (0) maps to database ID 81952

    Returns:
        The offset value (81952)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT MIN(id) FROM law_chunks")
        min_id = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return min_id if min_id else 81952

    except Exception as e:
        logger.error(f"Error getting mapping offset: {e}")
        return 81952  # Default offset


def map_faiss_to_db_id(faiss_index: int) -> int:
    """
    Map FAISS index to database ID

    Args:
        faiss_index: The FAISS vector index (0-based)

    Returns:
        The corresponding database ID
    """
    offset = get_mapping_offset()
    return offset + faiss_index


def test_retrieval():
    """Test the retrieval functions"""
    print("=== Testing Chunk Retrieval ===\n")

    # Test by database ID
    print("1. Testing retrieval by database ID (81952):")
    chunk = get_chunk_by_db_id(81952)
    if chunk:
        print(f"   Found: {chunk['section_title']}")
        print(f"   Text preview: {chunk['chunk_text'][:100]}...")
    else:
        print("   Not found")

    # Test by FAISS index
    print("\n2. Testing retrieval by FAISS index (0):")
    chunk = get_chunk_by_faiss_index(0)
    if chunk:
        print(f"   Found: {chunk['section_title']}")
        print(f"   DB ID: {chunk['db_id']}")
        print(f"   Text preview: {chunk['chunk_text'][:100]}...")
    else:
        print("   Not found")

    # Test batch retrieval
    print("\n3. Testing batch retrieval (indices 0, 1, 2):")
    chunks = get_chunks_by_faiss_indices([0, 1, 2])
    for i, chunk in enumerate(chunks):
        print(f"   Chunk {i}: {chunk['section_title']} (DB ID: {chunk['db_id']})")

    # Test mapping
    print("\n4. Testing FAISS to DB ID mapping:")
    for faiss_idx in [0, 100, 1000]:
        db_id = map_faiss_to_db_id(faiss_idx)
        print(f"   FAISS index {faiss_idx} -> DB ID {db_id}")


if __name__ == "__main__":
    test_retrieval()