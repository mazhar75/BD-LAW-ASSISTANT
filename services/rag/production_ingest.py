"""
Production Data Ingestion Pipeline
Properly stores data in PostgreSQL + FAISS with ID mapping
"""

import os
import sys
import json
import gzip
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from tqdm import tqdm
import time
from datetime import datetime
import numpy as np
import pickle
from dotenv import load_dotenv
import re

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from embeddings.embedding_generator import EmbeddingGenerator
from embeddings.vector_store import VectorStore
from chunking.document_chunker import DocumentChunker

# Load environment variables
load_dotenv('../../.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionIngestionPipeline:
    """Production-ready ingestion pipeline with PostgreSQL + FAISS"""

    def __init__(self):
        """Initialize pipeline with database connection"""
        # Database configuration from .env
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', 5432),
            'database': os.getenv('DB_NAME', 'bdlaw'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')  # Load from environment only
        }

        if not self.db_config['password']:
            raise ValueError("Database password not found in environment variables. Please set DB_PASSWORD in .env file")

        # Paths
        self.data_path = Path('../../data/raw')
        self.output_path = Path('../../data/processed')
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.embedding_gen = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        self.vector_store = VectorStore(
            dimension=self.embedding_gen.dimension,
            index_type="Flat",  # Use Flat for accurate search
            metric="cosine"
        )
        self.chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)

        # ID mapping: FAISS index -> PostgreSQL chunk_id
        self.index_to_chunk_id = {}
        self.chunk_id_to_index = {}

        # Statistics
        self.stats = {
            'total_files': 0,
            'total_documents': 0,
            'total_chunks': 0,
            'total_embeddings': 0,
            'failed_files': []
        }

        # Connect to database
        self.conn = None
        self.connect_db()

    def connect_db(self):
        """Establish PostgreSQL connection"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False
            logger.info(f"Connected to PostgreSQL database: {self.db_config['database']}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def verify_database(self):
        """Verify that required tables exist"""
        try:
            with self.conn.cursor() as cur:
                # Check if tables exist
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN ('laws', 'law_chunks', 'embeddings', 'query_logs')
                    ORDER BY table_name;
                """)

                tables = [row[0] for row in cur.fetchall()]

                required_tables = ['embeddings', 'law_chunks', 'laws', 'query_logs']
                missing = set(required_tables) - set(tables)

                if missing:
                    raise Exception(f"Missing tables: {missing}. Please run migrate_schema.py first")

                logger.info(f"✅ All required tables exist: {', '.join(tables)}")
                return True
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            raise

    def load_and_store_document(self, file_path: Path) -> Optional[int]:
        """
        Load document and store in PostgreSQL

        Returns:
            law_id if successful, None otherwise
        """
        try:
            # Read compressed markdown
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                content = f.read()

            # Load metadata
            meta_path = file_path.with_suffix('.meta.json')
            metadata = {}
            if meta_path.exists():
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            # Extract act number from filename
            act_number = int(file_path.stem.replace('act_', '').replace('.md', ''))

            # Extract title
            title = metadata.get('title', '')
            if not title:
                # Try to extract from content
                lines = content.split('\n')
                for line in lines[:10]:
                    if line.strip() and not line.startswith('#'):
                        title = line.strip()
                        break

            # Extract year
            year = None
            year_match = re.search(r'\b(18\d{2}|19\d{2}|20\d{2})\b', title + ' ' + content[:500])
            if year_match:
                year = int(year_match.group(1))

            # Categorize document
            category = self.categorize_document(title, content)

            # Insert into database
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO laws (
                        act_number, title, full_text, year, category,
                        language, url, scraped_at, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (act_number) DO UPDATE SET
                        title = EXCLUDED.title,
                        full_text = EXCLUDED.full_text,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    act_number,
                    title[:500] if title else f"Act {act_number}",
                    content,
                    year,
                    category,
                    'en',
                    metadata.get('url', ''),
                    metadata.get('crawled_at', datetime.now()),
                    json.dumps(metadata)
                ))
                law_id = cur.fetchone()[0]
                self.conn.commit()

                self.stats['total_documents'] += 1
                return law_id

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.conn.rollback()
            self.stats['failed_files'].append(str(file_path))
            return None

    def chunk_and_store(self, law_id: int, content: str, title: str) -> List[int]:
        """
        Chunk document and store chunks in PostgreSQL

        Returns:
            List of chunk_ids
        """
        try:
            # Generate chunks
            chunks = self.chunker.chunk_document(
                document_id=f"law_{law_id}",
                content=content,
                metadata={'law_id': law_id, 'title': title}
            )

            chunk_ids = []
            with self.conn.cursor() as cur:
                for idx, chunk in enumerate(chunks):
                    # Extract chunk content
                    chunk_text = chunk.content if hasattr(chunk, 'content') else chunk['content']

                    # Store chunk in database
                    cur.execute("""
                        INSERT INTO law_chunks (
                            law_id, chunk_index, chunk_text,
                            section_title, start_char, end_char, token_count
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        law_id,
                        idx,
                        chunk_text,
                        f"Chunk {idx + 1}",
                        chunk.start_index if hasattr(chunk, 'start_index') else idx * 400,
                        chunk.end_index if hasattr(chunk, 'end_index') else (idx + 1) * 400,
                        len(chunk_text.split())
                    ))
                    chunk_id = cur.fetchone()[0]
                    chunk_ids.append(chunk_id)

                self.conn.commit()
                self.stats['total_chunks'] += len(chunk_ids)
                return chunk_ids

        except Exception as e:
            logger.error(f"Error chunking law_id {law_id}: {e}")
            self.conn.rollback()
            return []

    def generate_and_store_embeddings(self, chunk_ids: List[int]) -> List[Tuple[int, np.ndarray]]:
        """
        Generate embeddings and store in PostgreSQL

        Returns:
            List of (chunk_id, embedding) tuples
        """
        embeddings_data = []

        try:
            with self.conn.cursor() as cur:
                for chunk_id in chunk_ids:
                    # Get chunk text
                    cur.execute("SELECT chunk_text FROM law_chunks WHERE id = %s", (chunk_id,))
                    result = cur.fetchone()
                    if not result:
                        continue

                    chunk_text = result[0]

                    # Generate embedding (returns 2D array, we need 1D)
                    embeddings = self.embedding_gen.generate(chunk_text)
                    embedding = embeddings[0] if len(embeddings.shape) > 1 else embeddings

                    # Store embedding in PostgreSQL
                    cur.execute("""
                        INSERT INTO embeddings (
                            chunk_id, model_name, embedding_vector, vector_dimension
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT (chunk_id, model_name) DO UPDATE SET
                            embedding_vector = EXCLUDED.embedding_vector,
                            created_at = CURRENT_TIMESTAMP
                    """, (
                        chunk_id,
                        self.embedding_gen.model_name,
                        pickle.dumps(embedding),  # Store as binary
                        self.embedding_gen.dimension
                    ))

                    embeddings_data.append((chunk_id, embedding))
                    self.stats['total_embeddings'] += 1

                self.conn.commit()
                return embeddings_data

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            self.conn.rollback()
            return []

    def add_to_faiss(self, embeddings_data: List[Tuple[int, np.ndarray]]):
        """
        Add embeddings to FAISS with ID mapping

        Args:
            embeddings_data: List of (chunk_id, embedding) tuples
        """
        for chunk_id, embedding in embeddings_data:
            # Get current FAISS index position
            faiss_idx = len(self.index_to_chunk_id)

            # Ensure embedding is a proper numpy array with correct shape
            if isinstance(embedding, list):
                embedding = np.array(embedding)

            # Reshape if needed (ensure 2D array for add_vectors)
            if len(embedding.shape) == 1:
                embedding = embedding.reshape(1, -1)

            # Add to FAISS (vector_store expects 2D numpy array)
            self.vector_store.add_vectors(
                embedding,
                [{'chunk_id': chunk_id}]
            )

            # Update ID mappings
            self.index_to_chunk_id[faiss_idx] = chunk_id
            self.chunk_id_to_index[chunk_id] = faiss_idx

    def categorize_document(self, title: str, content: str) -> str:
        """Categorize document based on content"""
        text = (title + ' ' + content[:1000]).lower()

        categories = {
            'criminal': ['criminal', 'penal', 'punishment', 'offense', 'crime'],
            'property': ['property', 'land', 'ownership', 'transfer', 'sale'],
            'contract': ['contract', 'agreement', 'obligation', 'breach'],
            'family': ['family', 'marriage', 'divorce', 'inheritance'],
            'constitutional': ['constitution', 'fundamental', 'rights'],
            'commercial': ['company', 'business', 'commercial', 'corporate']
        }

        for category, keywords in categories.items():
            if any(word in text for word in keywords):
                return category

        return 'general'

    def save_indices(self):
        """Save FAISS index and ID mappings"""
        # Save FAISS index
        faiss_path = self.output_path / 'faiss_index.bin'
        self.vector_store.save(str(faiss_path))
        logger.info(f"Saved FAISS index to {faiss_path}")

        # Save ID mappings
        mapping_path = self.output_path / 'id_mappings.pkl'
        with open(mapping_path, 'wb') as f:
            pickle.dump({
                'index_to_chunk_id': self.index_to_chunk_id,
                'chunk_id_to_index': self.chunk_id_to_index
            }, f)
        logger.info(f"Saved ID mappings to {mapping_path}")

        # Save ingestion metadata
        metadata_path = self.output_path / 'ingestion_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats,
                'embedding_model': self.embedding_gen.model_name,
                'embedding_dimension': self.embedding_gen.dimension,
                'total_mappings': len(self.index_to_chunk_id)
            }, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")

    def run(self, limit: Optional[int] = None):
        """
        Run the complete ingestion pipeline

        Args:
            limit: Optional limit on number of documents
        """
        start_time = time.time()
        logger.info("="*70)
        logger.info("Starting Production Data Ingestion Pipeline")
        logger.info(f"PostgreSQL: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
        logger.info("="*70)

        try:
            # Verify database tables exist
            self.verify_database()

            # Find all markdown files
            files = list(self.data_path.glob('acts/*.md.gz'))
            if limit:
                files = files[:limit]

            logger.info(f"Processing {len(files)} documents...")

            # Process each document
            for file_path in tqdm(files, desc="Ingesting documents"):
                self.stats['total_files'] += 1

                # 1. Load and store document in PostgreSQL
                law_id = self.load_and_store_document(file_path)
                if not law_id:
                    continue

                # 2. Get document content for chunking
                with self.conn.cursor() as cur:
                    cur.execute("SELECT full_text, title FROM laws WHERE id = %s", (law_id,))
                    result = cur.fetchone()
                    if not result:
                        continue

                content, title = result

                # 3. Chunk and store in PostgreSQL
                chunk_ids = self.chunk_and_store(law_id, content, title)

                # 4. Generate embeddings and store
                embeddings_data = self.generate_and_store_embeddings(chunk_ids)

                # 5. Add to FAISS with ID mapping
                self.add_to_faiss(embeddings_data)

            # Save indices and mappings
            self.save_indices()

            # Print summary
            elapsed = time.time() - start_time
            logger.info("\n" + "="*70)
            logger.info("INGESTION COMPLETE")
            logger.info("="*70)
            logger.info(f"Time: {elapsed:.2f} seconds")
            logger.info(f"Files processed: {self.stats['total_files']}")
            logger.info(f"Documents stored: {self.stats['total_documents']}")
            logger.info(f"Chunks created: {self.stats['total_chunks']}")
            logger.info(f"Embeddings generated: {self.stats['total_embeddings']}")
            logger.info(f"Failed files: {len(self.stats['failed_files'])}")
            logger.info(f"FAISS index size: {len(self.index_to_chunk_id)} vectors")
            logger.info("✅ Data successfully stored in PostgreSQL + FAISS")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="Production data ingestion")
    parser.add_argument("--limit", type=int, help="Limit number of documents")
    args = parser.parse_args()

    pipeline = ProductionIngestionPipeline()
    pipeline.run(limit=args.limit)


if __name__ == "__main__":
    main()