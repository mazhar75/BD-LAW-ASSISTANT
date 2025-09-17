"""
BD Law Assistant Scraper Package
"""

from scrapers.core.firecrawl_client import FirecrawlClient
from scrapers.core.queue_manager import RedisQueueManager
from scrapers.validators.content_validator import LegalDocumentValidator
from scrapers.storage.file_storage import DocumentStorage
from scrapers.bd_law_crawler import BDLawCrawler

__version__ = "1.0.0"
__all__ = [
    "FirecrawlClient",
    "RedisQueueManager",
    "LegalDocumentValidator",
    "DocumentStorage",
    "BDLawCrawler"
]