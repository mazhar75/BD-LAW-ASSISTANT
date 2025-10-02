"""
Database module for RAG service
"""

from .connection import DatabaseConnection, get_db_connection
from .models import Law, LawChunk, Embedding, QueryLog

__all__ = [
    'DatabaseConnection',
    'get_db_connection',
    'Law',
    'LawChunk',
    'Embedding',
    'QueryLog'
]