"""
File storage system for scraped legal documents
"""
import os
import json
import gzip
import shutil
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from scrapers.config.settings import get_settings
from scrapers.utils.logger import get_logger
from scrapers.core.firecrawl_client import CrawlResult


class DocumentStorage:
    """
    Scalable storage system for legal documents
    """

    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("storage")

        # Get storage directories
        self.storage_dirs = self.settings.storage.get_subdirs()

        # File naming conventions
        self.file_formats = {
            'raw': 'html',
            'markdown': 'md',
            'metadata': 'json',
            'compressed': 'gz'
        }

        # Initialize storage stats
        self.stats = {
            'files_stored': 0,
            'total_size_bytes': 0,
            'duplicates_skipped': 0
        }

        # Content hash cache for deduplication
        self.hash_cache = set()
        self._load_hash_cache()

    def _load_hash_cache(self):
        """Load existing content hashes for deduplication"""
        cache_file = self.settings.storage.data_dir / 'hash_cache.json'
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                self.hash_cache = set(json.load(f))
            self.logger.logger.info(f"Loaded {len(self.hash_cache)} content hashes")

    def _save_hash_cache(self):
        """Save content hash cache"""
        cache_file = self.settings.storage.data_dir / 'hash_cache.json'
        with open(cache_file, 'w') as f:
            json.dump(list(self.hash_cache), f)

    def _generate_filename(self, url: str, doc_type: str, format: str = 'html') -> str:
        """Generate standardized filename from URL"""
        # Extract key parts from URL
        if '/act-' in url or '/act-details-' in url:
            # Handle both old format (act-1) and new format (act-details-1)
            match = re.search(r'/act(?:-details)?-(\d+)', url)
            if match:
                return f"act_{match.group(1)}.{format}"
        elif '/volume-' in url:
            match = re.search(r'/volume-(\d+)', url)
            if match:
                return f"volume_{match.group(1)}.{format}"

        # Fallback to hash-based name
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"{doc_type}_{url_hash}.{format}"

    def _get_storage_path(self, url: str, content_type: str, language: str = 'english') -> Path:
        """Determine storage path based on content type and language"""
        if language == 'bengali':
            base_dir = self.storage_dirs['bengali']
        elif content_type == 'act':
            base_dir = self.storage_dirs['acts']
        elif content_type == 'volume':
            base_dir = self.storage_dirs['volumes']
        else:
            base_dir = self.settings.storage.raw_data_dir

        return base_dir

    def store_document(self, result: CrawlResult, validation_result: Optional[Dict] = None,
                       compress: bool = True) -> Tuple[str, int]:
        """
        Store scraped document with metadata

        Args:
            result: CrawlResult object
            validation_result: Validation results
            compress: Whether to compress the content

        Returns:
            Tuple of (file_path, file_size)
        """
        # Check for duplicates
        if result.content_hash in self.hash_cache:
            self.stats['duplicates_skipped'] += 1
            self.logger.logger.info(f"Skipping duplicate content for {result.url}")
            return None, 0

        # Determine storage location
        content_type = validation_result.get('content_type', 'unknown') if validation_result else 'unknown'
        language = validation_result.get('language', 'english') if validation_result else 'english'
        storage_dir = self._get_storage_path(result.url, content_type, language)

        # Generate filenames
        base_filename = self._generate_filename(result.url, content_type, format='')
        html_filename = base_filename + 'html'
        md_filename = base_filename + 'md'
        meta_filename = base_filename + 'meta.json'

        # Prepare metadata
        metadata = {
            'url': result.url,
            'crawled_at': result.crawled_at.isoformat(),
            'content_hash': result.content_hash,
            'content_type': content_type,
            'language': language,
            'original_metadata': result.metadata,
            'validation': validation_result,
            'file_paths': {
                'html': str(storage_dir / html_filename),
                'markdown': str(storage_dir / md_filename),
                'metadata': str(storage_dir / meta_filename)
            }
        }

        # Store files
        total_size = 0

        # Store HTML
        if result.html:
            html_path = storage_dir / html_filename
            if compress:
                html_path = html_path.with_suffix('.html.gz')
                with gzip.open(html_path, 'wt', encoding='utf-8') as f:
                    f.write(result.html)
            else:
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(result.html)
            total_size += html_path.stat().st_size

        # Store Markdown
        if result.content:
            md_path = storage_dir / md_filename
            if compress:
                md_path = md_path.with_suffix('.md.gz')
                with gzip.open(md_path, 'wt', encoding='utf-8') as f:
                    f.write(result.content)
            else:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(result.content)
            total_size += md_path.stat().st_size

        # Store metadata
        meta_path = storage_dir / meta_filename
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        total_size += meta_path.stat().st_size

        # Update stats
        self.stats['files_stored'] += 1
        self.stats['total_size_bytes'] += total_size
        self.hash_cache.add(result.content_hash)

        self.logger.log_storage(str(meta_path), total_size)

        return str(meta_path), total_size

    def store_batch(self, results: List[CrawlResult], validation_results: List[Dict] = None,
                   compress: bool = True) -> List[Tuple[str, int]]:
        """Store multiple documents"""
        stored_files = []

        if validation_results is None:
            validation_results = [None] * len(results)

        for result, validation in zip(results, validation_results):
            file_info = self.store_document(result, validation, compress)
            if file_info[0]:  # If not a duplicate
                stored_files.append(file_info)

        # Save hash cache after batch
        self._save_hash_cache()

        self.logger.logger.info(
            "batch_storage_complete",
            total_documents=len(results),
            stored=len(stored_files),
            duplicates_skipped=self.stats['duplicates_skipped'],
            total_size_mb=self.stats['total_size_bytes'] / (1024 * 1024)
        )

        return stored_files

    def create_parquet_archive(self, output_dir: Path = None) -> str:
        """
        Create Parquet archive of all stored documents for efficient querying

        Returns:
            Path to Parquet file
        """
        if output_dir is None:
            output_dir = self.settings.storage.processed_data_dir

        # Collect all metadata files
        metadata_files = list(self.settings.storage.raw_data_dir.rglob('*.meta.json'))

        documents = []
        for meta_file in metadata_files:
            with open(meta_file, 'r', encoding='utf-8') as f:
                doc = json.load(f)

                # Read associated markdown content
                md_file = meta_file.with_suffix('').with_suffix('.md')
                if md_file.exists():
                    with open(md_file, 'r', encoding='utf-8') as mf:
                        doc['content'] = mf.read()
                elif md_file.with_suffix('.md.gz').exists():
                    with gzip.open(md_file.with_suffix('.md.gz'), 'rt', encoding='utf-8') as mf:
                        doc['content'] = mf.read()

                documents.append(doc)

        # Create DataFrame
        df = pd.DataFrame(documents)

        # Create Parquet file with compression
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        parquet_path = output_dir / f'documents_{timestamp}.parquet'

        table = pa.Table.from_pandas(df)
        pq.write_table(
            table,
            parquet_path,
            compression='snappy',
            use_dictionary=True,
            compression_level=9
        )

        self.logger.logger.info(
            "parquet_archive_created",
            path=str(parquet_path),
            documents=len(documents),
            size_mb=parquet_path.stat().st_size / (1024 * 1024)
        )

        return str(parquet_path)

    def load_document(self, file_path: str) -> Dict:
        """Load a stored document"""
        meta_path = Path(file_path)

        if not meta_path.exists():
            return None

        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Load content if needed
        md_path = meta_path.with_suffix('').with_suffix('.md')
        if md_path.exists():
            with open(md_path, 'r', encoding='utf-8') as f:
                metadata['content'] = f.read()
        elif md_path.with_suffix('.md.gz').exists():
            with gzip.open(md_path.with_suffix('.md.gz'), 'rt', encoding='utf-8') as f:
                metadata['content'] = f.read()

        return metadata

    def search_documents(self, query: Dict) -> List[Dict]:
        """Search stored documents by metadata"""
        results = []

        # Search all metadata files
        for meta_file in self.settings.storage.raw_data_dir.rglob('*.meta.json'):
            with open(meta_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

                # Check query conditions
                match = True
                for key, value in query.items():
                    if key not in metadata or metadata[key] != value:
                        match = False
                        break

                if match:
                    results.append(metadata)

        return results

    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        # Calculate directory sizes
        dir_sizes = {}
        for name, path in self.storage_dirs.items():
            size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            dir_sizes[name] = size

        return {
            'files_stored': self.stats['files_stored'],
            'total_size_bytes': self.stats['total_size_bytes'],
            'duplicates_skipped': self.stats['duplicates_skipped'],
            'unique_documents': len(self.hash_cache),
            'directory_sizes': dir_sizes,
            'total_size_mb': self.stats['total_size_bytes'] / (1024 * 1024)
        }

    def cleanup_old_files(self, days: int = 30):
        """Remove files older than specified days"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        removed_count = 0

        for file_path in self.settings.storage.raw_data_dir.rglob('*'):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                removed_count += 1

        self.logger.logger.info(f"Removed {removed_count} old files")
        return removed_count