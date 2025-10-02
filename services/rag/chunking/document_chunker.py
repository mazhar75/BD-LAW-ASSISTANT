"""
Document Chunker - Split legal documents into searchable chunks
"""
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass
import hashlib

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter
)
from langchain.schema import Document as LangchainDocument

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a document chunk"""
    chunk_id: str
    document_id: str
    content: str
    metadata: Dict
    chunk_index: int
    start_char: int
    end_char: int

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'chunk_id': self.chunk_id,
            'document_id': self.document_id,
            'content': self.content,
            'metadata': self.metadata,
            'chunk_index': self.chunk_index,
            'start_char': self.start_char,
            'end_char': self.end_char
        }


class DocumentChunker:
    """Smart document chunking for legal texts"""

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 separators: Optional[List[str]] = None):
        """
        Initialize document chunker

        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators for splitting (defaults to legal document separators)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Default separators for legal documents
        if separators is None:
            separators = [
                "\n## ",  # Major sections
                "\n### ",  # Subsections
                "\n#### ",  # Sub-subsections
                "\n\n",   # Paragraphs
                "\n",     # Lines
                ". ",     # Sentences
                ", ",     # Clauses
                " ",      # Words
                ""        # Characters
            ]

        self.separators = separators

        # Initialize text splitters
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
            add_start_index=True  # Track position in original document
        )

        # For simple splitting (fallback)
        self.simple_splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator="\n\n",
            length_function=len
        )

        logger.info(f"DocumentChunker initialized: size={chunk_size}, overlap={chunk_overlap}")

    def generate_chunk_id(self, document_id: str, chunk_index: int, content: str) -> str:
        """
        Generate unique ID for a chunk

        Args:
            document_id: Parent document ID
            chunk_index: Index of chunk in document
            content: Chunk content

        Returns:
            Unique chunk ID
        """
        # Create hash from content for deduplication
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{document_id}_chunk_{chunk_index}_{content_hash}"

    def extract_section_headers(self, content: str) -> List[str]:
        """
        Extract section headers from markdown content

        Args:
            content: Markdown content

        Returns:
            List of section headers
        """
        headers = []
        pattern = r'^(#{1,4})\s+(.+)$'

        for line in content.split('\n'):
            match = re.match(pattern, line)
            if match:
                level = len(match.group(1))
                header = match.group(2).strip()
                headers.append((level, header))

        return headers

    def find_section_context(self, content: str, start_char: int) -> Dict[str, str]:
        """
        Find the section context for a given position in the document

        Args:
            content: Full document content
            start_char: Starting character position

        Returns:
            Dictionary with section context
        """
        # Find all headers before this position
        before_content = content[:start_char]
        headers = self.extract_section_headers(before_content)

        context = {}
        for level, header in headers:
            if level == 1:
                context['title'] = header
            elif level == 2:
                context['section'] = header
            elif level == 3:
                context['subsection'] = header
            elif level == 4:
                context['subsubsection'] = header

        return context

    def chunk_document(self,
                      document_id: str,
                      content: str,
                      metadata: Optional[Dict] = None,
                      method: str = 'recursive') -> List[Chunk]:
        """
        Chunk a single document

        Args:
            document_id: Unique identifier for the document
            content: Document content to chunk
            metadata: Optional metadata to attach to chunks
            method: Chunking method ('recursive' or 'simple')

        Returns:
            List of Chunk objects
        """
        if not content:
            logger.warning(f"Empty content for document {document_id}")
            return []

        metadata = metadata or {}
        chunks = []

        try:
            # Choose splitter based on method
            if method == 'recursive':
                splitter = self.recursive_splitter
            else:
                splitter = self.simple_splitter

            # Create Langchain document
            langchain_doc = LangchainDocument(
                page_content=content,
                metadata={'document_id': document_id, **metadata}
            )

            # Split document
            langchain_chunks = splitter.split_documents([langchain_doc])

            # Convert to our Chunk format
            for i, lc_chunk in enumerate(langchain_chunks):
                # Get position information
                start_char = lc_chunk.metadata.get('start_index', 0)
                end_char = start_char + len(lc_chunk.page_content)

                # Find section context
                section_context = self.find_section_context(content, start_char)

                # Create chunk metadata
                chunk_metadata = {
                    **metadata,
                    **section_context,
                    'chunk_index': i,
                    'total_chunks': len(langchain_chunks),
                    'method': method
                }

                # Create chunk
                chunk = Chunk(
                    chunk_id=self.generate_chunk_id(document_id, i, lc_chunk.page_content),
                    document_id=document_id,
                    content=lc_chunk.page_content,
                    metadata=chunk_metadata,
                    chunk_index=i,
                    start_char=start_char,
                    end_char=end_char
                )

                chunks.append(chunk)

            logger.debug(f"Created {len(chunks)} chunks for document {document_id}")

        except Exception as e:
            logger.error(f"Error chunking document {document_id}: {e}")
            # Fallback to simple splitting
            if method == 'recursive':
                logger.info("Falling back to simple chunking method")
                return self.chunk_document(document_id, content, metadata, method='simple')

        return chunks

    def chunk_legal_document(self,
                            act_number: int,
                            title: str,
                            content: str,
                            language: str = 'en') -> List[Chunk]:
        """
        Chunk a legal document with act-specific metadata

        Args:
            act_number: Act number
            title: Document title
            content: Document content
            language: Language code

        Returns:
            List of chunks
        """
        # Generate document ID
        document_id = f"act_{act_number}"

        # Prepare metadata
        metadata = {
            'act_number': act_number,
            'title': title,
            'language': language,
            'document_type': 'legal_act'
        }

        # Extract year if present
        year_match = re.search(r'\b(18\d{2}|19\d{2}|20\d{2})\b', title)
        if year_match:
            metadata['year'] = int(year_match.group(1))

        # Use appropriate chunk size based on language
        if language == 'bn':  # Bengali typically needs smaller chunks
            self.recursive_splitter.chunk_size = 800
            self.recursive_splitter.chunk_overlap = 150
        else:
            self.recursive_splitter.chunk_size = self.chunk_size
            self.recursive_splitter.chunk_overlap = self.chunk_overlap

        return self.chunk_document(document_id, content, metadata, method='recursive')

    def chunk_bengali_document(self,
                              title: str,
                              content: str,
                              source_path: str) -> List[Chunk]:
        """
        Chunk Bengali language document with special handling

        Args:
            title: Document title
            content: Bengali content
            source_path: Source file path

        Returns:
            List of chunks
        """
        # Generate document ID from source path
        path = Path(source_path)
        document_id = path.stem.replace('.md', '')

        # Prepare metadata
        metadata = {
            'title': title,
            'language': 'bn',
            'document_type': 'bengali_legal',
            'source_file': path.name
        }

        # Bengali-specific separators
        bengali_separators = [
            "।।",     # Bengali double danda (major separator)
            "।",      # Bengali danda (sentence end)
            "\n\n",   # Paragraphs
            "\n",     # Lines
            ", ",     # Commas
            " ",      # Words
            ""        # Characters
        ]

        # Create Bengali-specific splitter
        bengali_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Smaller chunks for Bengali
            chunk_overlap=150,
            separators=bengali_separators,
            length_function=len,
            add_start_index=True
        )

        # Temporarily use Bengali splitter
        original_splitter = self.recursive_splitter
        self.recursive_splitter = bengali_splitter

        try:
            chunks = self.chunk_document(document_id, content, metadata, method='recursive')
        finally:
            # Restore original splitter
            self.recursive_splitter = original_splitter

        return chunks

    def save_chunks(self, chunks: List[Chunk], output_dir: Optional[Path] = None):
        """
        Save chunks to JSON files

        Args:
            chunks: List of chunks to save
            output_dir: Directory to save chunks (defaults to processed/chunks)
        """
        if not chunks:
            return

        if output_dir is None:
            output_dir = Path("../../data/processed/chunks")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Group chunks by document ID
        document_chunks = {}
        for chunk in chunks:
            if chunk.document_id not in document_chunks:
                document_chunks[chunk.document_id] = []
            document_chunks[chunk.document_id].append(chunk)

        # Save each document's chunks
        for doc_id, doc_chunks in document_chunks.items():
            output_file = output_dir / f"{doc_id}_chunks.json"

            chunks_data = [chunk.to_dict() for chunk in doc_chunks]

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(doc_chunks)} chunks to {output_file}")

    def calculate_chunk_statistics(self, chunks: List[Chunk]) -> Dict:
        """
        Calculate statistics about chunks

        Args:
            chunks: List of chunks

        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {'total_chunks': 0}

        lengths = [len(chunk.content) for chunk in chunks]

        return {
            'total_chunks': len(chunks),
            'avg_chunk_size': sum(lengths) / len(lengths),
            'min_chunk_size': min(lengths),
            'max_chunk_size': max(lengths),
            'total_characters': sum(lengths),
            'unique_documents': len(set(chunk.document_id for chunk in chunks))
        }


def main():
    """Test document chunker"""
    import sys
    sys.path.append(str(Path(__file__).parent.parent))

    from ingestion.data_loader import DataLoader

    # Initialize components
    loader = DataLoader()
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)

    print("Testing Document Chunker")
    print("=" * 60)

    # Test with first act
    print("\n1. Testing with English Act:")
    doc = next(loader.load_acts(limit=1))
    chunks = chunker.chunk_legal_document(
        doc.act_number,
        doc.title,
        doc.content,
        doc.language
    )

    stats = chunker.calculate_chunk_statistics(chunks)
    print(f"   Document: {doc.title[:60]}...")
    print(f"   Original size: {len(doc.content)} chars")
    print(f"   Chunks created: {stats['total_chunks']}")
    print(f"   Avg chunk size: {stats['avg_chunk_size']:.0f} chars")

    # Show sample chunk
    if chunks:
        print(f"\n   Sample chunk metadata:")
        print(f"   - Chunk ID: {chunks[0].chunk_id}")
        print(f"   - Section: {chunks[0].metadata.get('section', 'N/A')}")
        print(f"   - Content preview: {chunks[0].content[:100]}...")

    # Test with Bengali document
    print("\n2. Testing with Bengali Document:")
    bengali_docs = list(loader.load_bengali_documents(limit=1))
    if bengali_docs:
        bengali_doc = bengali_docs[0]
        bengali_chunks = chunker.chunk_bengali_document(
            bengali_doc.title,
            bengali_doc.content,
            bengali_doc.source_path
        )

        bengali_stats = chunker.calculate_chunk_statistics(bengali_chunks)
        print(f"   Document: {bengali_doc.title[:60]}...")
        print(f"   Language: {bengali_doc.language}")
        print(f"   Chunks created: {bengali_stats['total_chunks']}")
    else:
        print("   No Bengali documents found")

    # Save test chunks
    print("\n3. Saving chunks to processed directory:")
    output_dir = Path("../../data/processed/chunks")
    chunker.save_chunks(chunks[:5], output_dir)  # Save first 5 chunks as test
    print(f"   Saved to {output_dir}")


if __name__ == "__main__":
    main()