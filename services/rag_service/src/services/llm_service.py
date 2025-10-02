"""
LLM Service
Handles interactions with Large Language Models (Gemini and OpenAI)
"""
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
import time

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"


class LLMService:
    """Service for interacting with LLMs (Gemini and OpenAI)"""

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.GEMINI,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs
    ):
        """
        Initialize LLM service

        Args:
            provider: LLM provider to use
            api_key: API key for the provider
            model: Model name
            temperature: Temperature for generation
            max_tokens: Maximum output tokens
            **kwargs: Additional provider-specific parameters
        """
        self.provider = provider
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs

        # Provider-specific clients
        self.gemini_client = None
        self.openai_client = None
        self.model = model

        # Initialize the appropriate client
        self._initialize_client()

        logger.info(f"LLM Service initialized with provider: {provider}")

    def _initialize_client(self):
        """Initialize the LLM client based on provider"""
        try:
            if self.provider == LLMProvider.GEMINI:
                self._init_gemini()
            elif self.provider == LLMProvider.OPENAI:
                self._init_openai()
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise

    def _init_gemini(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai

            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is required")

            genai.configure(api_key=self.api_key)

            # Set default model if not specified
            if not self.model:
                self.model = "gemini-2.5-flash"

            # Create model instance
            generation_config = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "top_p": self.kwargs.get("top_p", 0.95),
                "top_k": self.kwargs.get("top_k", 40),
            }

            self.gemini_client = genai.GenerativeModel(
                model_name=self.model,
                generation_config=generation_config
            )

            logger.info(f"Gemini client initialized with model: {self.model}")

        except ImportError:
            raise ImportError(
                "google-generativeai is not installed. "
                "Install with: pip install google-generativeai"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise

    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI

            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is required")

            self.openai_client = OpenAI(api_key=self.api_key)

            # Set default model if not specified
            if not self.model:
                self.model = "gpt-3.5-turbo"

            logger.info(f"OpenAI client initialized with model: {self.model}")

        except ImportError:
            raise ImportError(
                "openai is not installed. "
                "Install with: pip install openai"
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            raise

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate text using the LLM

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_retries: Maximum number of retries on failure

        Returns:
            Dictionary with response and metadata
        """
        for attempt in range(max_retries):
            try:
                start_time = time.time()

                if self.provider == LLMProvider.GEMINI:
                    result = self._generate_gemini(prompt, system_prompt)
                elif self.provider == LLMProvider.OPENAI:
                    result = self._generate_openai(prompt, system_prompt)
                else:
                    raise ValueError(f"Unsupported provider: {self.provider}")

                generation_time = time.time() - start_time

                return {
                    "text": result["text"],
                    "provider": self.provider.value,
                    "model": self.model,
                    "generation_time_ms": generation_time * 1000,
                    "token_count": result.get("token_count"),
                    "finish_reason": result.get("finish_reason"),
                    "metadata": result.get("metadata", {})
                }

            except Exception as e:
                logger.warning(
                    f"Generation attempt {attempt + 1}/{max_retries} failed: {e}"
                )
                if attempt == max_retries - 1:
                    logger.error(f"All generation attempts failed: {e}")
                    raise
                time.sleep(1 * (attempt + 1))  # Exponential backoff

    def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate using Google Gemini"""
        try:
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Generate content
            response = self.gemini_client.generate_content(full_prompt)

            return {
                "text": response.text,
                "token_count": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count
                    if hasattr(response, 'usage_metadata') else None,
                    "completion_tokens": response.usage_metadata.candidates_token_count
                    if hasattr(response, 'usage_metadata') else None,
                },
                "finish_reason": response.candidates[0].finish_reason.name
                if response.candidates else None,
                "metadata": {
                    "safety_ratings": [
                        {
                            "category": rating.category.name,
                            "probability": rating.probability.name
                        }
                        for rating in response.candidates[0].safety_ratings
                    ] if response.candidates else []
                }
            }

        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

    def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate using OpenAI"""
        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return {
                "text": response.choices[0].message.content,
                "token_count": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason,
                "metadata": {
                    "model": response.model,
                    "created": response.created
                }
            }

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Async version of generate (runs sync generate in executor)

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_retries: Maximum number of retries

        Returns:
            Dictionary with response and metadata
        """
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate(prompt, system_prompt, max_retries)
        )

    def generate_with_context(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate answer with provided context chunks

        Args:
            query: User query
            context_chunks: List of context chunks with text and metadata
            system_prompt: Optional system prompt

        Returns:
            Generated response with metadata
        """
        # Build context string
        context_str = self._format_context(context_chunks)

        # Build prompt
        prompt = self._build_rag_prompt(query, context_str)

        # Generate
        return self.generate(prompt, system_prompt)

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format context chunks into a readable string

        Args:
            chunks: List of chunks with metadata

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get('metadata', {})
            text = chunk.get('text', chunk.get('content', ''))

            # Build source attribution
            source = f"[Source {i}]"
            if metadata.get('title'):
                source += f" {metadata['title']}"
            if metadata.get('section_title'):
                source += f" - {metadata['section_title']}"
            if metadata.get('year'):
                source += f" ({metadata['year']})"

            context_parts.append(f"{source}\n{text}")

        return "\n\n".join(context_parts)

    def _build_rag_prompt(self, query: str, context: str) -> str:
        """
        Build RAG prompt with query and context

        Args:
            query: User query
            context: Formatted context string

        Returns:
            Complete prompt
        """
        return f"""Based on the following legal documents, please answer the question.

Context:
{context}

Question: {query}

Instructions:
- Provide a clear and accurate answer based on the context above
- Cite specific laws, sections, or articles when relevant
- If the context doesn't contain enough information, acknowledge the limitation
- Use clear legal language but make it understandable
- Include references to the source documents

Answer:"""

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        try:
            if self.provider == LLMProvider.OPENAI:
                import tiktoken
                encoding = tiktoken.encoding_for_model(self.model)
                return len(encoding.encode(text))
            else:
                # Rough estimation for other providers (4 chars ≈ 1 token)
                return len(text) // 4

        except Exception as e:
            logger.warning(f"Token counting failed: {e}. Using estimation.")
            return len(text) // 4

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model

        Returns:
            Model information dictionary
        """
        return {
            "provider": self.provider.value,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "initialized": (
                self.gemini_client is not None or
                self.openai_client is not None
            )
        }

    def __repr__(self) -> str:
        return (
            f"LLMService(provider={self.provider.value}, "
            f"model={self.model}, temperature={self.temperature})"
        )
