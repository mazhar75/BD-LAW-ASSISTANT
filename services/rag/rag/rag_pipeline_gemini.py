"""
RAG Pipeline for Bangladesh Law Assistant with Gemini Integration
Implements the main RAG pipeline using Google's Gemini API
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

# Google Generative AI
import google.generativeai as genai

# Load environment variables
load_dotenv()

try:
    # Try absolute imports first (for running from services/rag)
    from embeddings.embedding_generator import EmbeddingGenerator
    from embeddings.vector_store import VectorStore as FaissVectorStore
    from search.vector_search import VectorSearch
    from chunking.document_chunker import DocumentChunker
    from database.connection import DatabaseConnection
except ImportError:
    # Fallback to relative imports (for package usage)
    from ..embeddings.embedding_generator import EmbeddingGenerator
    from ..embeddings.vector_store import VectorStore as FaissVectorStore
    from ..search.vector_search import VectorSearch
    from ..chunking.document_chunker import DocumentChunker
    from ..database.connection import DatabaseConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""
    model_name: str = "gemini-1.5-flash"  # Updated to current available model
    temperature: float = 0.1
    max_output_tokens: int = 2048
    top_k: int = 5
    top_p: float = 0.95
    chunk_size: int = 1000
    chunk_overlap: int = 200
    verbose: bool = False


class RAGPipeline:
    """Main RAG pipeline for Bangladesh Law Assistant using Gemini"""

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.model = None
        self.vector_search = None
        self.db = DatabaseConnection()
        self.conversation_history = []

        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Initialize all components of the RAG pipeline"""
        logger.info("Initializing RAG pipeline with Gemini...")

        # Initialize Gemini
        self._setup_gemini()

        # Initialize vector search
        self._setup_vector_search()

        logger.info("RAG pipeline initialized successfully")

    def _setup_gemini(self):
        """Setup Google Gemini model"""
        try:
            # Configure Gemini with API key from environment
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")

            genai.configure(api_key=api_key)

            # Initialize the model
            generation_config = {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": 40,
                "max_output_tokens": self.config.max_output_tokens,
            }

            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]

            self.model = genai.GenerativeModel(
                self.config.model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            logger.info(f"Gemini model '{self.config.model_name}' initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise

    def _setup_vector_search(self):
        """Initialize vector search component"""
        try:
            # Initialize embedding generator
            embedding_gen = EmbeddingGenerator()

            # Initialize FAISS vector store
            vector_store = FaissVectorStore(
                dimension=embedding_gen.dimension,
                index_type="Flat"  # Using Flat for better accuracy
            )

            # Initialize vector search
            self.vector_search = VectorSearch(
                vector_store=vector_store,
                embedding_generator=embedding_gen
            )

            # Load existing index if available
            index_path = "../../data/processed/faiss_index.bin"
            if os.path.exists(index_path):
                self.vector_search.load_index(index_path)
                logger.info(f"Loaded FAISS index from {index_path}")
            else:
                logger.warning(f"FAISS index not found at {index_path}")

        except Exception as e:
            logger.error(f"Failed to setup vector search: {e}")
            raise

    def _retrieve_context(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Retrieve relevant context from vector search"""
        top_k = top_k or self.config.top_k

        try:
            # Perform hybrid search (semantic + keyword)
            results = self.vector_search.hybrid_search(
                query=query,
                top_k=top_k
                # Removed alpha parameter as it's not supported
            )

            if not results:
                logger.warning(f"No results found for query: {query}")

            return results

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []

    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into context string"""
        if not documents:
            return "No relevant legal documents found."

        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"Document {i}:")
            context_parts.append(f"Title: {doc.get('title', 'Unknown')}")
            context_parts.append(f"Year: {doc.get('year', 'Unknown')}")
            context_parts.append(f"Content: {doc.get('content', '')}")
            context_parts.append(f"Relevance Score: {doc.get('score', 0.0):.4f}")
            context_parts.append("-" * 40)

        return "\n".join(context_parts)

    def _create_prompt(self, query: str, context: str, use_chat: bool = False) -> str:
        """Create prompt for Gemini"""

        if use_chat and self.conversation_history:
            history = "\n".join([f"User: {q}\nAssistant: {a}" for q, a in self.conversation_history[-3:]])
            prompt = f"""You are a legal expert assistant specializing in Bangladesh law.

Previous conversation:
{history}

Current context from Bangladesh legal documents:
{context}

Current question: {query}

Instructions:
1. Answer based on the provided legal context
2. Cite specific laws, acts, or sections when applicable
3. If the context doesn't contain relevant information, say so clearly
4. Be precise and accurate in legal terminology
5. Consider the conversation history when relevant

Answer:"""
        else:
            prompt = f"""You are a legal expert assistant specializing in Bangladesh law.

Context from Bangladesh legal documents:
{context}

Question: {query}

Instructions:
1. Answer based ONLY on the provided context
2. Cite specific laws, acts, or sections mentioned in the context
3. If the context doesn't contain the answer, say "I don't have enough information in the provided documents to answer this question."
4. Be precise and accurate in legal terminology
5. Structure your answer clearly and concisely

Answer:"""

        return prompt

    def ask(self, query: str, session_id: Optional[str] = None, use_chat: bool = False) -> Dict[str, Any]:
        """
        Answer a question about Bangladesh law using RAG

        Args:
            query: The user's question
            session_id: Optional session ID for conversation tracking
            use_chat: Whether to use conversation history

        Returns:
            Dictionary containing answer and metadata
        """
        try:
            # Retrieve relevant context
            logger.info(f"Processing query: {query[:100]}...")
            documents = self._retrieve_context(query)

            # Format context
            context = self._format_context(documents)

            # Create prompt
            prompt = self._create_prompt(query, context, use_chat)

            # Generate response with Gemini
            response = self.model.generate_content(prompt)

            # Extract answer
            answer = response.text

            # Store in conversation history if using chat
            if use_chat:
                self.conversation_history.append((query, answer))
                # Keep only last 5 exchanges
                self.conversation_history = self.conversation_history[-5:]

            # Log query to database
            self._log_query(query, answer, documents, session_id)

            # Format response
            return {
                "answer": answer,
                "sources": self._format_sources(documents),
                "query": query,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "model": self.config.model_name,
                "documents_retrieved": len(documents)
            }

        except Exception as e:
            logger.error(f"Error in ask method: {e}")
            return {
                "answer": "I apologize, but I encountered an error while processing your question. Please try again.",
                "error": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat()
            }

    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format source documents for response"""
        formatted_sources = []
        for doc in documents[:5]:  # Limit to top 5 sources
            formatted_sources.append({
                "title": doc.get('title', 'Unknown'),
                "year": doc.get('year', 'Unknown'),
                "content_preview": doc.get('content', '')[:200] + "...",
                "relevance_score": doc.get('score', 0.0),
                "chunk_id": doc.get('chunk_id', ''),
                "language": doc.get('language', 'en')
            })
        return formatted_sources

    def _log_query(self, query: str, answer: str, documents: List[Dict[str, Any]], session_id: Optional[str]):
        """Log query to database for analytics"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO query_logs (query, answer, sources, session_id, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                query,
                answer[:1000],  # Truncate long answers
                len(documents),
                session_id,
                datetime.now()
            ))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to log query: {e}")

    def search_laws(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for relevant laws without generating an answer"""
        try:
            results = self._retrieve_context(query, top_k=top_k)
            return results
        except Exception as e:
            logger.error(f"Error searching laws: {e}")
            return []

    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_conversation_history(self) -> List[tuple]:
        """Get current conversation history"""
        return self.conversation_history.copy()


# Test function
if __name__ == "__main__":
    import asyncio

    async def test_rag():
        """Test the RAG pipeline with Gemini"""

        # Initialize pipeline
        rag = RAGPipeline()

        # Test queries
        test_queries = [
            "What are the penalties for theft in Bangladesh?",
            "How to register a company in Bangladesh?",
            "What are the labor laws regarding working hours?"
        ]

        for query in test_queries:
            print(f"\nQuery: {query}")
            print("-" * 50)

            response = rag.ask(query)

            print(f"Answer: {response['answer'][:500]}...")
            print(f"Sources: {len(response.get('sources', []))} documents")
            print(f"Model: {response.get('model', 'Unknown')}")
            print("-" * 50)

    # Run test
    asyncio.run(test_rag())