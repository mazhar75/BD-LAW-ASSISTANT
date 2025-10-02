"""
RAG Pipeline for Bangladesh Law Assistant
Implements the main RAG (Retrieval-Augmented Generation) pipeline using LangChain
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import Document, BaseRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

try:
    # Try absolute imports first (for running from services/rag)
    from embeddings.embedding_generator import EmbeddingGenerator
    from embeddings.vector_store import VectorStore as FaissVectorStore
    from search.vector_search import VectorSearch
    from chunking.document_chunker import DocumentChunker
    from rag.prompts import LEGAL_QA_PROMPT, LEGAL_CHAT_PROMPT, CONDENSE_QUESTION_PROMPT
except ImportError:
    # Fallback to relative imports (for package usage)
    from ..embeddings.embedding_generator import EmbeddingGenerator
    from ..embeddings.vector_store import VectorStore as FaissVectorStore
    from ..search.vector_search import VectorSearch
    from ..chunking.document_chunker import DocumentChunker
    from .prompts import LEGAL_QA_PROMPT, LEGAL_CHAT_PROMPT, CONDENSE_QUESTION_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""
    model_name: str = "gpt-4-turbo-preview"
    temperature: float = 0.1
    max_tokens: int = 2048
    top_k: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 200
    use_compression: bool = True
    use_memory: bool = True
    memory_key: str = "chat_history"
    streaming: bool = False
    verbose: bool = False
    fallback_model: str = "claude-3-haiku-20240307"


class BangladeshLawRetriever:
    """Custom retriever for Bangladesh law documents"""

    def __init__(self, vector_search: VectorSearch, top_k: int = 5):
        self.vector_search = vector_search
        self.top_k = top_k
        self.metadata = {}  # For compatibility

    def _get_relevant_documents(self, query: str) -> List[Document]:
        """Retrieve relevant documents for the query"""
        results = self.vector_search.hybrid_search(
            query=query,
            top_k=self.top_k,
            alpha=0.5  # Balance between semantic and keyword search
        )

        # Convert search results to LangChain Documents
        documents = []
        for result in results:
            doc = Document(
                page_content=result['content'],
                metadata={
                    'source': result.get('source', ''),
                    'title': result.get('title', ''),
                    'year': result.get('year', ''),
                    'score': result.get('score', 0.0),
                    'chunk_id': result.get('chunk_id', ''),
                    'language': result.get('language', 'en')
                }
            )
            documents.append(doc)

        return documents

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """Async version of document retrieval"""
        return self._get_relevant_documents(query)


class RAGPipeline:
    """Main RAG pipeline for Bangladesh Law Assistant"""

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.llm = None
        self.fallback_llm = None
        self.retriever = None
        self.qa_chain = None
        self.chat_chain = None
        self.memory = None
        self.vector_search = None

        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Initialize all components of the RAG pipeline"""
        logger.info("Initializing RAG pipeline...")

        # Initialize LLMs
        self._setup_llms()

        # Initialize vector search
        self._setup_vector_search()

        # Initialize retriever
        self._setup_retriever()

        # Initialize memory (if enabled)
        if self.config.use_memory:
            self._setup_memory()

        # Initialize chains
        self._setup_chains()

        logger.info("RAG pipeline initialized successfully")

    def _setup_llms(self):
        """Setup primary and fallback LLMs"""
        callback_manager = None
        if self.config.streaming:
            callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

        try:
            # Try to initialize primary LLM
            if "gpt" in self.config.model_name.lower():
                self.llm = ChatOpenAI(
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    callbacks=callback_manager,
                    streaming=self.config.streaming
                )
            elif "claude" in self.config.model_name.lower():
                self.llm = ChatAnthropic(
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    callbacks=callback_manager,
                    streaming=self.config.streaming
                )
            else:
                raise ValueError(f"Unsupported model: {self.config.model_name}")

        except Exception as e:
            logger.warning(f"Failed to initialize primary LLM: {e}")
            logger.info("Falling back to alternative model...")

            # Setup fallback LLM
            if "claude" in self.config.fallback_model.lower():
                self.llm = ChatAnthropic(
                    model=self.config.fallback_model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    callbacks=callback_manager,
                    streaming=self.config.streaming
                )
            else:
                self.llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    callbacks=callback_manager,
                    streaming=self.config.streaming
                )

    def _setup_vector_search(self):
        """Initialize vector search component"""
        try:
            # Initialize embedding generator
            embedding_gen = EmbeddingGenerator()

            # Initialize FAISS vector store
            vector_store = FaissVectorStore(
                dimension=embedding_gen.dimension,
                index_type="IVF"
            )

            # Initialize vector search
            self.vector_search = VectorSearch(
                vector_store=vector_store,
                embedding_generator=embedding_gen
            )

            # Load existing index if available
            index_path = "data/processed/faiss_index"
            if os.path.exists(index_path):
                self.vector_search.load_index(index_path)
                logger.info(f"Loaded FAISS index from {index_path}")

        except Exception as e:
            logger.error(f"Failed to setup vector search: {e}")
            raise

    def _setup_retriever(self):
        """Setup the document retriever"""
        # Create custom retriever
        base_retriever = BangladeshLawRetriever(
            vector_search=self.vector_search,
            top_k=self.config.top_k
        )

        # Add compression if enabled
        if self.config.use_compression and self.llm:
            compressor = LLMChainExtractor.from_llm(self.llm)
            self.retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=base_retriever
            )
        else:
            self.retriever = base_retriever

    def _setup_memory(self):
        """Setup conversation memory"""
        self.memory = ConversationBufferMemory(
            memory_key=self.config.memory_key,
            return_messages=True,
            output_key="answer"
        )

    def _setup_chains(self):
        """Setup QA and chat chains"""
        # Setup basic QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            verbose=self.config.verbose,
            chain_type_kwargs={
                "prompt": LEGAL_QA_PROMPT
            }
        )

        # Setup conversational chain if memory is enabled
        if self.config.use_memory:
            self.chat_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.retriever,
                memory=self.memory,
                return_source_documents=True,
                verbose=self.config.verbose,
                combine_docs_chain_kwargs={
                    "prompt": LEGAL_CHAT_PROMPT
                },
                condense_question_prompt=CONDENSE_QUESTION_PROMPT
            )

    def answer_question(self, question: str, use_chat: bool = False) -> Dict[str, Any]:
        """
        Answer a question about Bangladesh law

        Args:
            question: The user's question
            use_chat: Whether to use chat chain with memory

        Returns:
            Dictionary containing answer and source documents
        """
        try:
            if use_chat and self.chat_chain:
                result = self.chat_chain({"question": question})
            else:
                result = self.qa_chain({"query": question})

            # Format the response
            response = {
                "answer": result.get("answer", result.get("result", "")),
                "source_documents": self._format_sources(result.get("source_documents", [])),
                "question": question,
                "timestamp": datetime.now().isoformat()
            }

            return response

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "answer": "I apologize, but I encountered an error while processing your question. Please try again.",
                "error": str(e),
                "question": question,
                "timestamp": datetime.now().isoformat()
            }

    def _format_sources(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Format source documents for response"""
        formatted_sources = []
        for doc in documents:
            formatted_sources.append({
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": doc.metadata.get("score", 0.0)
            })
        return formatted_sources

    def search_similar_laws(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar laws without generating an answer"""
        try:
            results = self.vector_search.hybrid_search(
                query=query,
                top_k=top_k,
                alpha=0.5
            )
            return results
        except Exception as e:
            logger.error(f"Error searching laws: {e}")
            return []

    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add new documents to the vector store"""
        try:
            # Process documents
            for doc in documents:
                # Create chunks
                chunker = DocumentChunker()
                chunks = chunker.chunk_document(
                    doc['content'],
                    metadata={
                        'source': doc.get('source', ''),
                        'title': doc.get('title', ''),
                        'year': doc.get('year', ''),
                        'language': doc.get('language', 'en')
                    }
                )

                # Add chunks to vector store
                for chunk in chunks:
                    self.vector_search.add_document(
                        content=chunk['content'],
                        metadata=chunk['metadata']
                    )

            # Save updated index
            self.vector_search.save_index("data/processed/faiss_index")
            return True

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False

    def clear_memory(self):
        """Clear conversation memory"""
        if self.memory:
            self.memory.clear()

    def get_memory_history(self) -> List[Dict[str, str]]:
        """Get conversation history from memory"""
        if not self.memory:
            return []

        messages = self.memory.chat_memory.messages
        history = []
        for msg in messages:
            history.append({
                "type": msg.__class__.__name__,
                "content": msg.content
            })
        return history

    def update_config(self, **kwargs):
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Reinitialize if critical parameters changed
        if any(key in ['model_name', 'fallback_model'] for key in kwargs):
            self._initialize_pipeline()