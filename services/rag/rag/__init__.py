"""
RAG (Retrieval-Augmented Generation) module for Bangladesh Law Assistant
"""

from .rag_pipeline import RAGPipeline, RAGConfig, BangladeshLawRetriever
from .prompts import (
    LEGAL_QA_PROMPT,
    LEGAL_CHAT_PROMPT,
    CONDENSE_QUESTION_PROMPT,
    LEGAL_SUMMARY_PROMPT,
    LEGAL_COMPARISON_PROMPT,
    LEGAL_ANALYSIS_PROMPT,
    BENGALI_TRANSLATION_PROMPT,
    LEGAL_EXTRACTION_PROMPT,
    LEGAL_EXPLANATION_PROMPT,
    FALLBACK_PROMPT,
    PromptSelector
)
from .context_manager import ContextWindow, ContextWindowManager, DocumentRanker

__all__ = [
    'RAGPipeline',
    'RAGConfig',
    'BangladeshLawRetriever',
    'PromptSelector',
    'ContextWindow',
    'ContextWindowManager',
    'DocumentRanker',
    'LEGAL_QA_PROMPT',
    'LEGAL_CHAT_PROMPT',
    'CONDENSE_QUESTION_PROMPT',
    'LEGAL_SUMMARY_PROMPT',
    'LEGAL_COMPARISON_PROMPT',
    'LEGAL_ANALYSIS_PROMPT',
    'BENGALI_TRANSLATION_PROMPT',
    'LEGAL_EXTRACTION_PROMPT',
    'LEGAL_EXPLANATION_PROMPT',
    'FALLBACK_PROMPT'
]

__version__ = '1.0.0'