"""
Data Loader - Load and parse legal documents from data directory
"""
import gzip
import json
from pathlib import Path
from typing import List, Dict, Optional, Iterator, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a legal document"""
    act_number: int
    title: str
    content: str
    metadata: Dict
    source_path: str
    language: str = "en"
    document_type: str = "act"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'act_number': self.act_number,
            'title': self.title,
            'content': self.content,
            'metadata': self.metadata,
            'source_path': self.source_path,
            'language': self.language,
            'document_type': self.document_type
        }


class DataLoader:
    """Load legal documents from various sources"""

    def __init__(self, data_dir: str = None):
        """
        Initialize data loader

        Args:
            data_dir: Root data directory path
        """
        self.data_dir = Path(data_dir) if data_dir else Path("../../data")
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"

        # Ensure directories exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        (self.processed_dir / "chunks").mkdir(exist_ok=True)
        (self.processed_dir / "metadata").mkdir(exist_ok=True)

        logger.info(f"DataLoader initialized with data_dir: {self.data_dir}")

    def load_gzipped_file(self, file_path: Path) -> str:
        """
        Load and decompress a gzipped file

        Args:
            file_path: Path to .gz file

        Returns:
            Decompressed content as string
        """
        try:
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            raise

    def load_json_file(self, file_path: Path) -> Dict:
        """
        Load JSON metadata file

        Args:
            file_path: Path to .json file

        Returns:
            Parsed JSON as dictionary
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON {file_path}: {e}")
            return {}

    def extract_title_from_content(self, content: str) -> str:
        """
        Extract title from markdown content

        Args:
            content: Markdown content

        Returns:
            Extracted title
        """
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove common prefixes
                import re
                title = re.sub(r'^Act\s+\d+\s*[-:]?\s*', '', line, flags=re.IGNORECASE)
                return title.strip()
        return "Unknown Document"

    def load_act(self, act_number: int) -> Optional[Document]:
        """
        Load a single act by number

        Args:
            act_number: Act number to load

        Returns:
            Document object or None if not found
        """
        acts_dir = self.raw_dir / "acts"

        # File paths
        md_file = acts_dir / f"act_{act_number}.md.gz"
        meta_file = acts_dir / f"act_{act_number}.meta.json"

        if not md_file.exists():
            logger.warning(f"Act {act_number} not found at {md_file}")
            return None

        try:
            # Load content
            content = self.load_gzipped_file(md_file)

            # Load metadata
            metadata = self.load_json_file(meta_file) if meta_file.exists() else {}

            # Extract title
            title = metadata.get('title') or self.extract_title_from_content(content)

            # Create document
            doc = Document(
                act_number=act_number,
                title=title,
                content=content,
                metadata=metadata,
                source_path=str(md_file),
                language=metadata.get('language', 'en'),
                document_type='act'
            )

            logger.debug(f"Loaded act {act_number}: {title[:50]}...")
            return doc

        except Exception as e:
            logger.error(f"Error loading act {act_number}: {e}")
            return None

    def load_acts(self,
                  start: Optional[int] = None,
                  end: Optional[int] = None,
                  limit: Optional[int] = None) -> Iterator[Document]:
        """
        Load multiple acts

        Args:
            start: Starting act number
            end: Ending act number (inclusive)
            limit: Maximum number of acts to load

        Yields:
            Document objects
        """
        acts_dir = self.raw_dir / "acts"

        # Find all act files
        act_files = sorted(acts_dir.glob("act_*.md.gz"))
        logger.info(f"Found {len(act_files)} act files")

        count = 0
        for act_file in act_files:
            if limit and count >= limit:
                break

            # Extract act number from filename (act_1.md.gz -> stem is act_1.md)
            try:
                # Remove .md extension from stem, then get the number
                base_name = act_file.stem.replace('.md', '')
                act_number = int(base_name.split('_')[1])
            except (IndexError, ValueError):
                logger.warning(f"Skipping invalid filename: {act_file.name}")
                continue

            # Apply filters
            if start and act_number < start:
                continue
            if end and act_number > end:
                continue

            # Load document
            doc = self.load_act(act_number)
            if doc:
                yield doc
                count += 1

    def load_bengali_documents(self, limit: Optional[int] = None) -> Iterator[Document]:
        """
        Load Bengali language documents

        Args:
            limit: Maximum number of documents to load

        Yields:
            Document objects
        """
        bengali_dir = self.raw_dir / "bengali"

        if not bengali_dir.exists():
            logger.warning(f"Bengali directory not found: {bengali_dir}")
            return

        count = 0
        for md_file in sorted(bengali_dir.glob("*.md.gz")):
            if limit and count >= limit:
                break

            try:
                # Load content
                content = self.load_gzipped_file(md_file)

                # Load metadata if exists
                meta_file = md_file.with_suffix('.meta.json')
                metadata = self.load_json_file(meta_file) if meta_file.exists() else {}

                # Extract title
                title = metadata.get('title') or self.extract_title_from_content(content)

                # Create document
                doc = Document(
                    act_number=0,  # No act number for Bengali docs
                    title=title,
                    content=content,
                    metadata=metadata,
                    source_path=str(md_file),
                    language='bn',  # Bengali language code
                    document_type='bengali'
                )

                yield doc
                count += 1

            except Exception as e:
                logger.error(f"Error loading Bengali document {md_file}: {e}")
                continue

    def load_all_documents(self,
                          include_acts: bool = True,
                          include_bengali: bool = True,
                          limit: Optional[int] = None) -> Iterator[Document]:
        """
        Load all documents from various sources

        Args:
            include_acts: Include English acts
            include_bengali: Include Bengali documents
            limit: Maximum total documents to load

        Yields:
            Document objects
        """
        total_count = 0

        # Load acts
        if include_acts:
            for doc in self.load_acts():
                if limit and total_count >= limit:
                    return
                yield doc
                total_count += 1

        # Load Bengali documents
        if include_bengali:
            remaining = limit - total_count if limit else None
            for doc in self.load_bengali_documents(limit=remaining):
                yield doc
                total_count += 1

    def get_document_stats(self) -> Dict:
        """
        Get statistics about available documents

        Returns:
            Dictionary with document counts
        """
        stats = {
            'total_acts': 0,
            'total_bengali': 0,
            'total_volumes': 0,
            'total_documents': 0
        }

        # Count acts
        acts_dir = self.raw_dir / "acts"
        if acts_dir.exists():
            stats['total_acts'] = len(list(acts_dir.glob("act_*.md.gz")))

        # Count Bengali documents
        bengali_dir = self.raw_dir / "bengali"
        if bengali_dir.exists():
            stats['total_bengali'] = len(list(bengali_dir.glob("*.md.gz")))

        # Count volumes
        volumes_dir = self.raw_dir / "volumes"
        if volumes_dir.exists():
            stats['total_volumes'] = len(list(volumes_dir.glob("*.md.gz")))

        stats['total_documents'] = (
            stats['total_acts'] +
            stats['total_bengali'] +
            stats['total_volumes']
        )

        return stats

    def save_processed_metadata(self, doc: Document, chunks_info: List[Dict]):
        """
        Save metadata about processed document and its chunks

        Args:
            doc: Original document
            chunks_info: Information about generated chunks
        """
        metadata = {
            'act_number': doc.act_number,
            'title': doc.title,
            'source_path': doc.source_path,
            'language': doc.language,
            'document_type': doc.document_type,
            'processed_at': datetime.now().isoformat(),
            'num_chunks': len(chunks_info),
            'chunks': chunks_info
        }

        # Save to processed metadata directory
        meta_file = self.processed_dir / "metadata" / f"{doc.document_type}_{doc.act_number}.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved metadata for {doc.title} to {meta_file}")


def main():
    """Test data loader functionality"""
    loader = DataLoader()

    # Get statistics
    stats = loader.get_document_stats()
    print("Document Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nLoading first 3 acts:")
    for doc in loader.load_acts(limit=3):
        print(f"  - Act {doc.act_number}: {doc.title[:60]}...")
        print(f"    Content length: {len(doc.content)} chars")

    print("\nLoading first 2 Bengali documents:")
    for doc in loader.load_bengali_documents(limit=2):
        print(f"  - {doc.title[:60]}...")
        print(f"    Language: {doc.language}")


if __name__ == "__main__":
    main()