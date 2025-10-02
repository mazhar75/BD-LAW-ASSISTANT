"""
Database setup script for RAG service
"""
import sys
import os
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import DatabaseConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables(db: DatabaseConnection):
    """Create database tables from schema"""
    schema_file = Path(__file__).parent / "schema.sql"

    if not schema_file.exists():
        logger.error(f"Schema file not found: {schema_file}")
        return False

    try:
        # Read and execute schema
        with open(schema_file, 'r') as f:
            schema_sql = f.read()

        with db.get_cursor(dict_cursor=False) as cursor:
            cursor.execute(schema_sql)

        logger.info("Database schema created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create schema: {str(e)}")
        return False


def verify_tables(db: DatabaseConnection):
    """Verify that all required tables exist"""
    required_tables = ['laws', 'law_chunks', 'embeddings', 'query_logs']

    for table in required_tables:
        if db.table_exists(table):
            columns = db.get_table_info(table)
            logger.info(f"✓ Table '{table}' exists with {len(columns)} columns")
        else:
            logger.error(f"✗ Table '{table}' does not exist")
            return False

    return True


def test_operations(db: DatabaseConnection):
    """Test basic database operations"""
    try:
        # Test insert
        insert_query = """
        INSERT INTO laws (act_number, title, full_text, year, category, language, url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (act_number) DO UPDATE
        SET title = EXCLUDED.title
        RETURNING id
        """

        with db.get_cursor() as cursor:
            cursor.execute(insert_query, (
                9999,
                "Test Act",
                "This is a test law document for verification.",
                2024,
                "Test",
                "en",
                "http://test.com"
            ))
            result = cursor.fetchone()
            law_id = result['id']
            logger.info(f"✓ Insert test passed, law_id: {law_id}")

        # Test select
        laws = db.execute_query("SELECT * FROM laws WHERE act_number = %s", (9999,))
        if laws:
            logger.info(f"✓ Select test passed, found {len(laws)} records")

        # Test update
        rows = db.execute_update(
            "UPDATE laws SET category = %s WHERE act_number = %s",
            ("Test Updated", 9999)
        )
        logger.info(f"✓ Update test passed, {rows} rows updated")

        # Clean up test data
        rows = db.execute_update("DELETE FROM laws WHERE act_number = %s", (9999,))
        logger.info(f"✓ Delete test passed, {rows} rows deleted")

        return True

    except Exception as e:
        logger.error(f"Test operations failed: {str(e)}")
        return False


def main():
    """Main setup function"""
    logger.info("="*60)
    logger.info("BD Law Assistant - Database Setup")
    logger.info("="*60)

    # Create database connection
    db = DatabaseConnection()

    # Test connection
    logger.info("\n1. Testing database connection...")
    if not db.test_connection():
        logger.error("Failed to connect to database")
        logger.info("\nMake sure PostgreSQL is running and configured:")
        logger.info("  - Host: " + db.host)
        logger.info("  - Port: " + str(db.port))
        logger.info("  - Database: " + db.database)
        logger.info("  - User: " + db.user)
        return False

    logger.info("✓ Database connection successful")

    # Create tables
    logger.info("\n2. Creating database tables...")
    if not create_tables(db):
        return False

    # Verify tables
    logger.info("\n3. Verifying tables...")
    if not verify_tables(db):
        return False

    # Test operations
    logger.info("\n4. Testing database operations...")
    if not test_operations(db):
        return False

    logger.info("\n" + "="*60)
    logger.info("✓ Database setup completed successfully!")
    logger.info("="*60)

    # Close connection
    db.close()
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)