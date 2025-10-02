"""
RAG Pipeline Service
Orchestrates retrieval and generation for question answering
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import time

from services.rag_service import RAGService
from services.llm_service import LLMService, LLMProvider
from config.settings import settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    RAG Pipeline for question answering
    Combines retrieval (RAG service) and generation (LLM service)
    """

    def __init__(
        self,
        rag_service: Optional[RAGService] = None,
        llm_service: Optional[LLMService] = None,
        llm_provider: LLMProvider = LLMProvider.GEMINI,
        context_top_k: int = None,
        min_similarity_score: float = None,
        enable_reranking: bool = None
    ):
        """
        Initialize RAG pipeline

        Args:
            rag_service: RAG service instance for retrieval
            llm_service: LLM service instance for generation
            llm_provider: LLM provider to use
            context_top_k: Number of chunks to retrieve
            min_similarity_score: Minimum similarity score threshold
            enable_reranking: Whether to enable context reranking
        """
        # Initialize RAG service
        self.rag_service = rag_service or RAGService()

        # Initialize LLM service
        if llm_service is None:
            api_key = (
                settings.GEMINI_API_KEY if llm_provider == LLMProvider.GEMINI
                else settings.OPENAI_API_KEY
            )
            model = (
                settings.GEMINI_MODEL if llm_provider == LLMProvider.GEMINI
                else settings.OPENAI_MODEL
            )
            temperature = (
                settings.GEMINI_TEMPERATURE if llm_provider == LLMProvider.GEMINI
                else settings.OPENAI_TEMPERATURE
            )
            max_tokens = (
                settings.GEMINI_MAX_OUTPUT_TOKENS if llm_provider == LLMProvider.GEMINI
                else settings.OPENAI_MAX_TOKENS
            )

            self.llm_service = LLMService(
                provider=llm_provider,
                api_key=api_key,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            self.llm_service = llm_service

        # Configuration
        self.context_top_k = context_top_k or settings.RAG_CONTEXT_TOP_K
        self.min_similarity_score = min_similarity_score or settings.RAG_MIN_SIMILARITY_SCORE
        self.enable_reranking = enable_reranking if enable_reranking is not None else settings.RAG_ENABLE_RERANKING

        logger.info(
            f"RAG Pipeline initialized with provider={llm_provider.value}, "
            f"top_k={self.context_top_k}, min_score={self.min_similarity_score}"
        )

    def answer_question(
        self,
        question: str,
        language: str = "en",
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG

        Args:
            question: User's question
            language: Query language
            top_k: Number of context chunks to retrieve
            filters: Optional metadata filters
            include_sources: Whether to include source documents

        Returns:
            Dictionary with answer, sources, and metadata
        """
        start_time = time.time()

        try:
            # Step 1: Retrieve relevant context
            retrieval_start = time.time()
            context_chunks = self._retrieve_context(
                question,
                language=language,
                top_k=top_k,
                filters=filters
            )
            retrieval_time = (time.time() - retrieval_start) * 1000

            if not context_chunks:
                return self._build_no_results_response(question, retrieval_time)

            # Step 2: Rerank context if enabled
            if self.enable_reranking:
                context_chunks = self._rerank_context(question, context_chunks)

            # Step 3: Filter by similarity score
            context_chunks = self._filter_by_score(context_chunks)

            if not context_chunks:
                return self._build_no_results_response(question, retrieval_time)

            # Step 4: Generate answer using LLM
            generation_start = time.time()
            answer_result = self._generate_answer(question, context_chunks, language)
            generation_time = (time.time() - generation_start) * 1000

            # Step 5: Build response
            total_time = (time.time() - start_time) * 1000

            response = {
                "question": question,
                "answer": answer_result["text"],
                "confidence": self._calculate_confidence(context_chunks),
                "sources": self._format_sources(context_chunks) if include_sources else [],
                "metadata": {
                    "total_time_ms": total_time,
                    "retrieval_time_ms": retrieval_time,
                    "generation_time_ms": generation_time,
                    "documents_found": len(context_chunks),
                    "llm_provider": answer_result.get("provider"),
                    "llm_model": answer_result.get("model"),
                    "token_count": answer_result.get("token_count"),
                    "language": language
                },
                "timestamp": datetime.now(timezone.utc)
            }

            logger.info(
                f"Question answered successfully in {total_time:.2f}ms "
                f"(retrieval: {retrieval_time:.2f}ms, generation: {generation_time:.2f}ms)"
            )

            return response

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return self._build_error_response(question, str(e))

    def _retrieve_context(
        self,
        query: str,
        language: str = "en",
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context chunks

        Args:
            query: Search query
            language: Query language
            top_k: Number of results
            filters: Optional filters

        Returns:
            List of context chunks with metadata
        """
        k = top_k or self.context_top_k

        # Extract filter parameters
        category = None
        year_min = None
        year_max = None

        if filters:
            category = filters.get('category')
            year_min = filters.get('year_min')
            year_max = filters.get('year_max')

        # Search using RAG service
        search_results = self.rag_service.search(
            query=query,
            top_k=k,
            language=language,
            category=category,
            year_min=year_min,
            year_max=year_max
        )

        # Convert to context format
        context_chunks = []
        for result in search_results:
            context_chunks.append({
                "text": result.content,
                "score": result.score,
                "metadata": {
                    "chunk_id": result.chunk_id,
                    "act_number": result.act_number,
                    "title": result.title,
                    "section_title": result.section,
                    "year": result.metadata.get('year') if result.metadata else None,
                    "category": result.metadata.get('category') if result.metadata else None,
                    "language": result.metadata.get('language') if result.metadata else language
                }
            })

        logger.debug(f"Retrieved {len(context_chunks)} context chunks")
        return context_chunks

    def _rerank_context(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rerank context chunks for better relevance

        Args:
            query: Original query
            context_chunks: List of context chunks

        Returns:
            Reranked list of chunks
        """
        # Simple reranking: prioritize chunks with higher scores
        # and penalize very long chunks
        for chunk in context_chunks:
            # Base score
            base_score = chunk['score']

            # Length penalty (prefer moderate length)
            text_length = len(chunk['text'])
            if text_length > 1000:
                length_penalty = 0.9
            elif text_length < 100:
                length_penalty = 0.95
            else:
                length_penalty = 1.0

            # Recency bonus (if year is available)
            year = chunk['metadata'].get('year')
            recency_bonus = 1.0
            if year and year >= 2020:
                recency_bonus = 1.05
            elif year and year >= 2010:
                recency_bonus = 1.02

            # Calculate final score
            chunk['rerank_score'] = base_score * length_penalty * recency_bonus

        # Sort by rerank score
        context_chunks.sort(key=lambda x: x.get('rerank_score', x['score']), reverse=True)

        logger.debug("Context chunks reranked")
        return context_chunks

    def _filter_by_score(
        self,
        context_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter chunks by minimum similarity score

        Args:
            context_chunks: List of chunks

        Returns:
            Filtered list
        """
        filtered = [
            chunk for chunk in context_chunks
            if chunk['score'] >= self.min_similarity_score
        ]

        logger.debug(
            f"Filtered {len(context_chunks)} chunks to {len(filtered)} "
            f"(threshold: {self.min_similarity_score})"
        )

        return filtered

    def _generate_answer(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Generate answer using LLM

        Args:
            question: User question
            context_chunks: Retrieved context
            language: Query language

        Returns:
            Generated answer with metadata
        """
        # Build system prompt
        system_prompt = self._build_system_prompt(language)

        # Generate using LLM
        result = self.llm_service.generate_with_context(
            query=question,
            context_chunks=context_chunks,
            system_prompt=system_prompt
        )

        return result

    def _build_system_prompt(self, language: str = "en") -> str:
        """
        Build system prompt for LLM

        Args:
            language: Target language

        Returns:
            System prompt string
        """
        if language == "bn":
            return """আপনি বাংলাদেশ আইন বিষয়ক একজন সহায়ক। আপনার কাজ হল:
- প্রদত্ত আইন দলিলের উপর ভিত্তি করে সঠিক এবং স্পষ্ট উত্তর দেওয়া
- নির্দিষ্ট আইন, ধারা বা অনুচ্ছেদ উল্লেখ করা
- যদি প্রদত্ত তথ্যে পর্যাপ্ত তথ্য না থাকে, তা স্বীকার করা
- আইনি ভাষা ব্যবহার করা কিন্তু বোধগম্য রাখা
- উৎস দলিলের রেফারেন্স অন্তর্ভুক্ত করা"""
        else:
            return """You are a legal assistant for Bangladesh law. Your role is to:
- Provide accurate and clear answers based on the provided legal documents
- Cite specific laws, sections, or articles when relevant
- Acknowledge limitations if the provided information is insufficient
- Use clear legal language while remaining understandable
- Include references to source documents"""

    def _calculate_confidence(self, context_chunks: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence score based on retrieval quality

        Args:
            context_chunks: Retrieved chunks

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not context_chunks:
            return 0.0

        # Average of top 3 scores
        top_scores = [chunk['score'] for chunk in context_chunks[:3]]
        avg_score = sum(top_scores) / len(top_scores)

        # Confidence based on number of sources
        source_bonus = min(len(context_chunks) / self.context_top_k, 1.0) * 0.1

        # Final confidence
        confidence = min(avg_score + source_bonus, 1.0)

        return round(confidence, 3)

    def _format_sources(
        self,
        context_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format source information

        Args:
            context_chunks: Context chunks

        Returns:
            List of formatted sources
        """
        sources = []

        for i, chunk in enumerate(context_chunks, 1):
            metadata = chunk['metadata']
            sources.append({
                "source_number": i,
                "title": metadata.get('title', 'Unknown'),
                "act_number": metadata.get('act_number'),
                "section": metadata.get('section_title'),
                "year": metadata.get('year'),
                "category": metadata.get('category'),
                "relevance_score": round(chunk['score'], 3),
                "excerpt": chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text']
            })

        return sources

    def _build_no_results_response(
        self,
        question: str,
        retrieval_time: float
    ) -> Dict[str, Any]:
        """
        Build response when no results found

        Args:
            question: Original question
            retrieval_time: Time spent on retrieval

        Returns:
            No results response
        """
        return {
            "question": question,
            "answer": "I couldn't find relevant information in the legal documents to answer your question. Please try rephrasing your question or using different keywords.",
            "confidence": 0.0,
            "sources": [],
            "metadata": {
                "total_time_ms": retrieval_time,
                "retrieval_time_ms": retrieval_time,
                "generation_time_ms": 0,
                "documents_found": 0,
                "language": "en"
            },
            "timestamp": datetime.now(timezone.utc)
        }

    def _build_error_response(
        self,
        question: str,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Build error response

        Args:
            question: Original question
            error_message: Error message

        Returns:
            Error response
        """
        return {
            "question": question,
            "answer": "An error occurred while processing your question. Please try again.",
            "confidence": 0.0,
            "sources": [],
            "metadata": {
                "error": error_message,
                "total_time_ms": 0,
                "retrieval_time_ms": 0,
                "generation_time_ms": 0,
                "documents_found": 0
            },
            "timestamp": datetime.now(timezone.utc)
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        language: str = "en",
        context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Conversational interface with history

        Args:
            messages: List of message dicts with 'role' and 'content'
            language: Language for response
            context: Optional pre-retrieved context

        Returns:
            Response with answer and sources
        """
        # Get the latest user message
        user_messages = [m for m in messages if m.get('role') == 'user']
        if not user_messages:
            return self._build_error_response("", "No user message found")

        latest_question = user_messages[-1]['content']

        # Build context from conversation history
        conversation_context = self._build_conversation_context(messages[:-1])

        # Answer the question
        response = self.answer_question(
            question=latest_question,
            language=language,
            include_sources=True
        )

        # Add conversation context to metadata
        response['metadata']['conversation_turn'] = len(user_messages)

        return response

    def _build_conversation_context(
        self,
        messages: List[Dict[str, str]]
    ) -> str:
        """
        Build conversation context string

        Args:
            messages: Previous messages

        Returns:
            Formatted context string
        """
        if not messages:
            return ""

        context_parts = []
        for msg in messages[-3:]:  # Last 3 turns
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            context_parts.append(f"{role.title()}: {content}")

        return "\n".join(context_parts)

    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Get information about the pipeline configuration

        Returns:
            Pipeline configuration info
        """
        return {
            "llm": self.llm_service.get_model_info(),
            "rag": self.rag_service.get_stats(),
            "config": {
                "context_top_k": self.context_top_k,
                "min_similarity_score": self.min_similarity_score,
                "enable_reranking": self.enable_reranking
            }
        }

    def __repr__(self) -> str:
        return (
            f"RAGPipeline(llm={self.llm_service.provider.value}, "
            f"top_k={self.context_top_k}, reranking={self.enable_reranking})"
        )
