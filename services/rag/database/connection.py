"""
PostgreSQL Database Connection Manager
"""
import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Dict, Any, Optional
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """PostgreSQL connection pool manager"""

    def __init__(self,
                 host: str = None,
                 port: int = None,
                 database: str = None,
                 user: str = None,
                 password: str = None,
                 min_conn: int = 1,
                 max_conn: int = 10):
        """
        Initialize database connection pool

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            min_conn: Minimum connections in pool
            max_conn: Maximum connections in pool
        """
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = port or int(os.getenv('DB_PORT', 5432))
        self.database = database or os.getenv('DB_NAME', 'bdlaw')
        self.user = user or os.getenv('DB_USER', 'bdlaw')
        self.password = password or os.getenv('DB_PASSWORD', 'bdlaw123')

        self.min_conn = min_conn
        self.max_conn = max_conn
        self.pool = None

    def connect(self):
        """Create connection pool"""
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                self.min_conn,
                self.max_conn,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"Database connection pool created for {self.database}@{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {str(e)}")
            raise

    def close(self):
        """Close all connections in pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")

    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """
        Get a database cursor from the pool

        Args:
            dict_cursor: Return results as dictionaries

        Yields:
            Database cursor
        """
        if not self.pool:
            self.connect()

        conn = None
        cursor = None
        try:
            conn = self.pool.getconn()
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.putconn(conn)

    def execute_query(self, query: str, params: tuple = None) -> list:
        """
        Execute a SELECT query

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query results as list of dictionaries
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Number of affected rows
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_script(self, script_path: str):
        """
        Execute a SQL script file

        Args:
            script_path: Path to SQL script
        """
        script = Path(script_path).read_text()

        with self.get_cursor(dict_cursor=False) as cursor:
            cursor.execute(script)
            logger.info(f"Executed script: {script_path}")

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            result = self.execute_query("SELECT 1")
            return len(result) > 0
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def get_table_info(self, table_name: str) -> list:
        """
        Get information about a table

        Args:
            table_name: Name of the table

        Returns:
            List of column information
        """
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
        """
        return self.execute_query(query, (table_name,))

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists

        Args:
            table_name: Name of the table

        Returns:
            True if table exists
        """
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = %s
        )
        """
        result = self.execute_query(query, (table_name,))
        return result[0]['exists'] if result else False


# Global connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """
    Get or create global database connection

    Returns:
        DatabaseConnection instance
    """
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
        _db_connection.connect()
    return _db_connection


def close_db_connection():
    """Close global database connection"""
    global _db_connection
    if _db_connection:
        _db_connection.close()
        _db_connection = None