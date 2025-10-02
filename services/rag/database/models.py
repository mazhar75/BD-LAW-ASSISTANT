"""
Database models for RAG service
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
import json


@dataclass
class Law:
    """Model for laws table"""
    id: Optional[int] = None
    act_number: int = None
    title: str = None
    title_bengali: Optional[str] = None
    full_text: str = None
    full_text_bengali: Optional[str] = None
    year: Optional[int] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    language: str = 'en'
    url: Optional[str] = None
    scraped_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'act_number': self.act_number,
            'title': self.title,
            'title_bengali': self.title_bengali,
            'full_text': self.full_text,
            'full_text_bengali': self.full_text_bengali,
            'year': self.year,
            'category': self.category,
            'subcategory': self.subcategory,
            'language': self.language,
            'url': self.url,
            'is_active': self.is_active
        }

        if self.metadata:
            data['metadata'] = json.dumps(self.metadata)

        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> 'Law':
        """Create from dictionary"""
        if data.get('metadata') and isinstance(data['metadata'], str):
            data['metadata'] = json.loads(data['metadata'])
        return cls(**data)


@dataclass
class LawChunk:
    """Model for law_chunks table"""
    id: Optional[int] = None
    law_id: int = None
    chunk_index: int = None
    chunk_text: str = None
    chunk_text_bengali: Optional[str] = None
    section_title: Optional[str] = None
    section_number: Optional[str] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    token_count: Optional[int] = None
    language: str = 'en'
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'law_id': self.law_id,
            'chunk_index': self.chunk_index,
            'chunk_text': self.chunk_text,
            'chunk_text_bengali': self.chunk_text_bengali,
            'section_title': self.section_title,
            'section_number': self.section_number,
            'start_char': self.start_char,
            'end_char': self.end_char,
            'token_count': self.token_count,
            'language': self.language
        }
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> 'LawChunk':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class Embedding:
    """Model for embeddings table"""
    id: Optional[int] = None
    chunk_id: int = None
    model_name: str = None
    embedding_vector: bytes = None  # Binary representation
    vector_dimension: int = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'chunk_id': self.chunk_id,
            'model_name': self.model_name,
            'embedding_vector': self.embedding_vector,
            'vector_dimension': self.vector_dimension
        }
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> 'Embedding':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class QueryLog:
    """Model for query_logs table"""
    id: Optional[int] = None
    query_text: str = None
    query_language: str = 'en'
    response_text: Optional[str] = None
    relevant_chunks: Optional[List[Dict]] = None
    model_used: Optional[str] = None
    response_time_ms: Optional[int] = None
    user_feedback: Optional[int] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'query_text': self.query_text,
            'query_language': self.query_language,
            'response_text': self.response_text,
            'model_used': self.model_used,
            'response_time_ms': self.response_time_ms,
            'user_feedback': self.user_feedback,
            'session_id': self.session_id,
            'ip_address': self.ip_address
        }

        if self.relevant_chunks:
            data['relevant_chunks'] = json.dumps(self.relevant_chunks)

        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> 'QueryLog':
        """Create from dictionary"""
        if data.get('relevant_chunks') and isinstance(data['relevant_chunks'], str):
            data['relevant_chunks'] = json.loads(data['relevant_chunks'])
        return cls(**data)