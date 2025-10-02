"""
Context Window Manager for handling long documents in RAG pipeline
Manages token limits and implements smart truncation strategies
"""

import tiktoken
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContextWindow:
    """Configuration for context window management"""
    max_tokens: int = 3000  # Max tokens for context
    max_tokens_per_doc: int = 500  # Max tokens per document
    preserve_ratio: float = 0.8  # Ratio of tokens to preserve from beginning
    model_name: str = "gpt-4"  # Model for tokenization


class ContextWindowManager:
    """Manages context window for LLM calls with long documents"""

    def __init__(self, config: Optional[ContextWindow] = None):
        self.config = config or ContextWindow()
        self.encoding = self._get_encoding()

    def _get_encoding(self):
        """Get the appropriate tokenizer for the model"""
        try:
            # Try to get encoding for specific model
            if "gpt-4" in self.config.model_name:
                return tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5" in self.config.model_name:
                return tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                # Default to cl100k_base encoding
                return tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to get model-specific encoding: {e}")
            return tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback to approximate count (1 token ≈ 4 characters)
            return len(text) // 4

    def manage_context(self, documents: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Manage context window by intelligently selecting and truncating documents

        Args:
            documents: List of documents with content and metadata
            query: User query

        Returns:
            List of documents that fit within context window
        """
        query_tokens = self.count_tokens(query)
        available_tokens = self.config.max_tokens - query_tokens - 100  # Reserve 100 for formatting

        if available_tokens <= 0:
            logger.warning("Query too long for context window")
            return []

        managed_docs = []
        total_tokens = 0

        # Sort documents by relevance score if available
        sorted_docs = sorted(
            documents,
            key=lambda x: x.get('metadata', {}).get('score', 0),
            reverse=True
        )

        for doc in sorted_docs:
            content = doc.get('content', doc.get('page_content', ''))
            doc_tokens = self.count_tokens(content)

            # Check if adding this document would exceed limit
            if total_tokens + doc_tokens > available_tokens:
                # Try to fit partial document
                remaining_tokens = available_tokens - total_tokens
                if remaining_tokens > 100:  # Only include if meaningful content
                    truncated_content = self._truncate_content(content, remaining_tokens)
                    managed_docs.append({
                        **doc,
                        'content': truncated_content,
                        'truncated': True
                    })
                    break
            else:
                # Check if document needs truncation based on per-doc limit
                if doc_tokens > self.config.max_tokens_per_doc:
                    truncated_content = self._truncate_content(content, self.config.max_tokens_per_doc)
                    managed_docs.append({
                        **doc,
                        'content': truncated_content,
                        'truncated': True
                    })
                    total_tokens += self.config.max_tokens_per_doc
                else:
                    managed_docs.append(doc)
                    total_tokens += doc_tokens

        logger.info(f"Context window: {len(managed_docs)} docs, {total_tokens} tokens")
        return managed_docs

    def _truncate_content(self, content: str, max_tokens: int) -> str:
        """
        Intelligently truncate content to fit within token limit

        Args:
            content: Original content
            max_tokens: Maximum allowed tokens

        Returns:
            Truncated content
        """
        # Split content into sections
        sections = self._split_into_sections(content)

        if not sections:
            # Simple truncation if no sections found
            return self._simple_truncate(content, max_tokens)

        # Smart truncation preserving structure
        return self._smart_truncate(sections, max_tokens)

    def _split_into_sections(self, content: str) -> List[str]:
        """Split content into logical sections"""
        # Try different section markers
        markers = ["\n\n", "\n", ". ", ", "]

        for marker in markers:
            sections = content.split(marker)
            if len(sections) > 1:
                # Rejoin with marker
                return [s + marker for s in sections[:-1]] + [sections[-1]]

        return [content]

    def _simple_truncate(self, content: str, max_tokens: int) -> str:
        """Simple truncation based on token count"""
        tokens = self.encoding.encode(content)

        if len(tokens) <= max_tokens:
            return content

        # Preserve beginning and end
        preserve_start = int(max_tokens * self.config.preserve_ratio)
        preserve_end = max_tokens - preserve_start

        truncated_tokens = tokens[:preserve_start]
        if preserve_end > 0:
            truncated_tokens.extend(tokens[-preserve_end:])
            middle_indicator = self.encoding.encode("\n... [content truncated] ...\n")
            truncated_tokens = (
                tokens[:preserve_start] +
                middle_indicator +
                tokens[-preserve_end:]
            )

        return self.encoding.decode(truncated_tokens)

    def _smart_truncate(self, sections: List[str], max_tokens: int) -> str:
        """Smart truncation preserving document structure"""
        result = []
        total_tokens = 0
        important_sections = []
        regular_sections = []

        # Classify sections by importance
        for section in sections:
            # Check if section contains important legal markers
            if any(marker in section.lower() for marker in
                   ["section", "article", "clause", "subsection", "penalty", "shall", "must"]):
                important_sections.append(section)
            else:
                regular_sections.append(section)

        # Add important sections first
        for section in important_sections:
            section_tokens = self.count_tokens(section)
            if total_tokens + section_tokens <= max_tokens:
                result.append(section)
                total_tokens += section_tokens
            elif total_tokens < max_tokens * 0.7:  # Still room for partial section
                remaining = max_tokens - total_tokens
                truncated = self._simple_truncate(section, remaining // 2)
                result.append(truncated)
                total_tokens += self.count_tokens(truncated)
                break

        # Fill remaining space with regular sections
        for section in regular_sections:
            section_tokens = self.count_tokens(section)
            if total_tokens + section_tokens <= max_tokens:
                result.append(section)
                total_tokens += section_tokens
            else:
                break

        return ''.join(result)

    def chunk_for_context(self, content: str, chunk_size: int = 1000) -> List[str]:
        """
        Chunk content into pieces that fit within token limits

        Args:
            content: Content to chunk
            chunk_size: Target chunk size in tokens

        Returns:
            List of content chunks
        """
        chunks = []
        tokens = self.encoding.encode(content)

        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

        return chunks

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """
        Estimate cost based on token usage

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Dictionary with cost estimates
        """
        # Approximate costs per 1K tokens (varies by model)
        cost_map = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "claude-3": {"input": 0.015, "output": 0.075}
        }

        model_key = "gpt-4"  # Default
        for key in cost_map.keys():
            if key in self.config.model_name.lower():
                model_key = key
                break

        costs = cost_map[model_key]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }

    def optimize_for_model(self, model_name: str) -> None:
        """
        Optimize context window settings for specific model

        Args:
            model_name: Name of the model
        """
        # Model-specific context window sizes
        model_contexts = {
            "gpt-4": 8000,
            "gpt-4-32k": 32000,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4000,
            "gpt-3.5-turbo-16k": 16000,
            "claude-3": 100000,
            "claude-2": 100000
        }

        for model, context_size in model_contexts.items():
            if model in model_name.lower():
                # Set to 70% of model's context to leave room for response
                self.config.max_tokens = int(context_size * 0.7)
                self.config.model_name = model_name
                self.encoding = self._get_encoding()
                logger.info(f"Optimized for {model} with {self.config.max_tokens} token context")
                break


class DocumentRanker:
    """Rank and reorder documents for optimal context usage"""

    @staticmethod
    def rank_documents(documents: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Rank documents based on relevance and importance

        Args:
            documents: List of documents to rank
            query: User query

        Returns:
            Ranked list of documents
        """
        scored_docs = []

        for doc in documents:
            score = 0
            content = doc.get('content', doc.get('page_content', '')).lower()
            query_lower = query.lower()

            # Check for exact query match
            if query_lower in content:
                score += 10

            # Check for query terms
            query_terms = query_lower.split()
            for term in query_terms:
                if term in content:
                    score += 1

            # Boost for legal importance indicators
            importance_markers = ['shall', 'must', 'required', 'penalty', 'violation', 'prohibited']
            for marker in importance_markers:
                if marker in content:
                    score += 0.5

            # Consider existing relevance score
            existing_score = doc.get('metadata', {}).get('score', 0)
            score += existing_score * 5

            # Add recency bonus if available
            year = doc.get('metadata', {}).get('year')
            if year:
                try:
                    year_int = int(year)
                    if year_int > 2020:
                        score += 2
                    elif year_int > 2010:
                        score += 1
                except:
                    pass

            scored_docs.append((score, doc))

        # Sort by score (descending)
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        return [doc for _, doc in scored_docs]


# Export classes
__all__ = ['ContextWindow', 'ContextWindowManager', 'DocumentRanker']