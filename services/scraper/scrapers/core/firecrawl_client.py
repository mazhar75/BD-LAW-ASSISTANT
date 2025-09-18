"""
Firecrawl API client with retry logic and error handling
"""
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import hashlib
import re
from bs4 import BeautifulSoup
import html2text

from firecrawl import Firecrawl
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

from scrapers.config.settings import get_settings
from scrapers.utils.logger import get_logger


@dataclass
class CrawlResult:
    """Data class for crawl results"""
    url: str
    content: str
    html: str
    metadata: Dict[str, Any]
    crawled_at: datetime
    content_hash: str
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'url': self.url,
            'content': self.content,
            'html': self.html,
            'metadata': self.metadata,
            'crawled_at': self.crawled_at.isoformat(),
            'content_hash': self.content_hash,
            'success': self.success,
            'error': self.error
        }


class FirecrawlClient:
    """
    Firecrawl API client with enhanced features for production use
    """

    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("firecrawl_client")

        # Initialize Firecrawl
        self.app = Firecrawl(api_key=self.settings.firecrawl.api_key)

        # Track rate limiting
        self.last_request_time = 0
        self.rate_limit_delay = self.settings.crawler.rate_limit

        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_bytes': 0
        }

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            self.logger.log_rate_limit(wait_time)
            time.sleep(wait_time)

        self.last_request_time = time.time()

    def _calculate_hash(self, content: str) -> str:
        """Calculate content hash for deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _convert_html_to_markdown(self, html_content: str) -> str:
        """Convert HTML to clean markdown for legal documents"""
        if not html_content:
            return ''

        try:
            # First try with html2text
            converter = html2text.HTML2Text()
            converter.ignore_links = False
            converter.ignore_images = True
            converter.ignore_emphasis = False
            converter.body_width = 0  # Don't wrap lines
            converter.unicode_snob = True
            converter.skip_internal_links = True
            converter.protect_links = True
            converter.wrap_links = False

            # Convert directly first
            markdown = converter.handle(html_content)

            # If result is too short or empty, try BeautifulSoup extraction
            if len(markdown.strip()) < 100:
                soup = BeautifulSoup(html_content, 'html.parser')

                # Remove unwanted elements
                for element in soup(["script", "style", "meta", "link", "noscript", "header", "nav", "footer"]):
                    element.decompose()

                # Try to extract main content
                main_text = soup.get_text(separator='\n', strip=True)

                # If we have substantial text, use it
                if len(main_text) > 100:
                    markdown = main_text

            # Clean up the markdown
            if markdown:
                # Remove excessive newlines
                markdown = re.sub(r'\n{3,}', '\n\n', markdown)

                # Remove common navigation/UI elements
                lines = []
                for line in markdown.split('\n'):
                    # Skip empty lines and navigation elements
                    line = line.strip()
                    if line and not any(skip in line.lower() for skip in [
                        'search by text', 'navbar', 'footer', 'copyright',
                        'powered by', 'login', 'logout', 'home page',
                        'javascript', 'enable javascript'
                    ]):
                        lines.append(line)

                markdown = '\n'.join(lines)

            return markdown.strip()

        except Exception as e:
            self.logger.logger.warning(f"Markdown conversion error: {e}")
            # Fallback: extract plain text
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                for element in soup(["script", "style", "meta", "link"]):
                    element.decompose()
                return soup.get_text(separator='\n', strip=True)
            except:
                return html_content  # Last resort: return original

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError))
    )
    def scrape_url(self, url: str, **options) -> CrawlResult:
        """
        Scrape a single URL with retry logic

        Args:
            url: URL to scrape
            **options: Additional Firecrawl options

        Returns:
            CrawlResult object
        """
        self._rate_limit()
        self.stats['total_requests'] += 1

        start_time = time.time()
        self.logger.log_scrape_start(url)

        try:
            # Perform scrape using Firecrawl's scrape method
            # First try JSON extraction for legal documents
            if 'bdlaws.minlaw.gov.bd' in url:
                # Use JSON extraction for Bangladesh law site
                result = self.app.scrape(
                    url,
                    formats=[
                        {
                            "type": "json",
                            "prompt": "Extract the complete legal document including: 1) The full act title 2) ALL section numbers and section titles 3) The COMPLETE text content of each section including all paragraphs, subsections, clauses, and provisos. Do not summarize - extract all text verbatim."
                        },
                        "html"  # Also get HTML as backup
                    ],
                    timeout=120000,
                    **options
                )
            else:
                # Standard scrape for other sites
                result = self.app.scrape(
                    url,
                    formats=['markdown', 'html'],
                    timeout=120000,
                    **options
                )

            # Handle response according to Firecrawl docs
            # Check if we have JSON extraction result for BD laws site
            if hasattr(result, 'json') and result.json:
                # Convert JSON to markdown format
                json_data = result.json
                markdown_lines = []

                # Add title if present
                if isinstance(json_data, dict):
                    if 'actTitle' in json_data:
                        markdown_lines.append(f"# {json_data['actTitle']}\n")

                    # Add sections
                    if 'sections' in json_data:
                        for section in json_data['sections']:
                            if 'sectionTitle' in section:
                                markdown_lines.append(f"\n## {section['sectionTitle']}\n")
                            if 'sectionContent' in section:
                                markdown_lines.append(f"{section['sectionContent']}\n")

                    # Handle other fields
                    for key, value in json_data.items():
                        if key not in ['actTitle', 'sections'] and value:
                            if isinstance(value, str):
                                markdown_lines.append(f"\n### {key}\n{value}\n")
                            elif isinstance(value, list):
                                markdown_lines.append(f"\n### {key}\n")
                                for item in value:
                                    markdown_lines.append(f"- {item}\n")

                content = '\n'.join(markdown_lines)
                html = result.html if hasattr(result, 'html') else ''
                metadata = result.metadata.__dict__ if hasattr(result, 'metadata') and hasattr(result.metadata, '__dict__') else {}

            elif hasattr(result, 'markdown'):
                # Standard markdown response
                content = result.markdown or ''
                html = result.html or ''
                metadata = result.metadata.__dict__ if hasattr(result.metadata, '__dict__') else {}
            elif isinstance(result, dict):
                # Dictionary response
                if 'data' in result:
                    data = result['data']
                    content = data.get('markdown', '')
                    html = data.get('html', '')
                    metadata = data.get('metadata', {})
                else:
                    content = result.get('markdown', '')
                    html = result.get('html', '')
                    metadata = result.get('metadata', {})
            else:
                raise ValueError(f"Invalid response from Firecrawl for {url}")

            # Check if markdown is actually HTML (common issue with Firecrawl)
            if content and ('DOCTYPE' in content[:200] or
                          '<html' in content[:200] or
                          '<meta' in content[:500] or
                          '�' in content[:100]):
                self.logger.logger.info(f"Markdown contains HTML for {url}, converting...")

                # Debug: check what we have
                self.logger.logger.debug(f"Content field has {len(content)} chars")
                self.logger.logger.debug(f"HTML field has {len(html) if html else 0} chars")

                # Priority: Use HTML field if it's longer/better quality
                if html and len(html) > len(content):
                    html_to_convert = html
                    self.logger.logger.info("Using HTML field for conversion")
                else:
                    html_to_convert = content
                    self.logger.logger.info("Using markdown field (contains HTML) for conversion")

                # Convert to proper markdown
                converted = self._convert_html_to_markdown(html_to_convert)

                # If conversion gave us good content, use it
                if converted and len(converted) > 100:
                    content = converted
                    self.logger.logger.info(f"Converted to {len(content)} chars of clean markdown")
                else:
                    # Fallback: Just extract plain text if conversion failed
                    self.logger.logger.warning("Conversion failed, trying direct text extraction")
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_to_convert, 'html.parser')

                    # Remove script/style tags
                    for tag in soup(['script', 'style', 'meta', 'link']):
                        tag.decompose()

                    content = soup.get_text(separator='\n', strip=True)
                    self.logger.logger.info(f"Extracted {len(content)} chars of text")

            # Calculate metrics
            duration = time.time() - start_time
            content_size = len(content.encode('utf-8'))
            self.stats['total_bytes'] += content_size

            # Create result object
            crawl_result = CrawlResult(
                url=url,
                content=content,
                html=html,
                metadata=metadata,
                crawled_at=datetime.now(),
                content_hash=self._calculate_hash(content),
                success=True
            )

            self.stats['successful_requests'] += 1
            self.logger.log_scrape_success(
                url=url,
                size=content_size,
                duration=duration,
                hash=crawl_result.content_hash
            )

            return crawl_result

        except Exception as e:
            self.stats['failed_requests'] += 1
            self.logger.log_scrape_error(url, e)

            return CrawlResult(
                url=url,
                content='',
                html='',
                metadata={},
                crawled_at=datetime.now(),
                content_hash='',
                success=False,
                error=str(e)
            )

    def crawl_website(self, start_url: str, **options) -> List[CrawlResult]:
        """
        Crawl entire website starting from a URL

        Args:
            start_url: Starting URL for crawl
            **options: Crawl options

        Returns:
            List of CrawlResult objects
        """
        self.logger.logger.info("website_crawl_started", url=start_url)

        results = []

        try:
            # Use Firecrawl's crawl method with proper options
            crawl_job = self.app.crawl(
                url=start_url,
                limit=options.get('limit', 100),
                scrape_options={
                    'formats': ['markdown', 'html']
                },
                poll_interval=2,
                timeout=120
            )

            if not crawl_job or 'data' not in crawl_job:
                raise ValueError("Invalid crawl response from Firecrawl")

            # Process results
            total_pages = len(crawl_job['data'])
            self.logger.logger.info("crawl_completed", total_pages=total_pages)

            for i, page_data in enumerate(crawl_job['data']):
                # Rate limiting between processing
                if i > 0 and i % 10 == 0:
                    self._rate_limit()

                try:
                    result = CrawlResult(
                        url=page_data.get('url', ''),
                        content=page_data.get('markdown', ''),
                        html=page_data.get('html', ''),
                        metadata=page_data.get('metadata', {}),
                        crawled_at=datetime.now(),
                        content_hash=self._calculate_hash(page_data.get('markdown', '')),
                        success=True
                    )
                    results.append(result)

                    self.logger.logger.info(
                        "page_processed",
                        url=result.url,
                        index=i + 1,
                        total=total_pages
                    )

                except Exception as e:
                    self.logger.logger.error(
                        "page_processing_failed",
                        url=page_data.get('url', 'unknown'),
                        error=str(e)
                    )

        except Exception as e:
            self.logger.logger.error("crawl_failed", error=str(e))
            raise

        return results

    def batch_scrape(self, urls: List[str], batch_size: int = None) -> List[CrawlResult]:
        """
        Scrape multiple URLs in batches

        Args:
            urls: List of URLs to scrape
            batch_size: Number of URLs per batch

        Returns:
            List of CrawlResult objects
        """
        if batch_size is None:
            batch_size = self.settings.crawler.batch_size

        results = []
        total_urls = len(urls)

        self.logger.logger.info("batch_scrape_started", total_urls=total_urls, batch_size=batch_size)

        for i in range(0, total_urls, batch_size):
            batch = urls[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_urls + batch_size - 1) // batch_size

            self.logger.logger.info(
                "processing_batch",
                batch_number=batch_num,
                total_batches=total_batches,
                batch_size=len(batch)
            )

            for url in batch:
                result = self.scrape_url(url)
                results.append(result)

            # Rate limit between batches
            if batch_num < total_batches:
                self._rate_limit()

        self.logger.logger.info(
            "batch_scrape_completed",
            total_scraped=len(results),
            successful=sum(1 for r in results if r.success),
            failed=sum(1 for r in results if not r.success)
        )

        return results

    def get_statistics(self) -> Dict:
        """Get client statistics"""
        success_rate = 0
        if self.stats['total_requests'] > 0:
            success_rate = self.stats['successful_requests'] / self.stats['total_requests']

        return {
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'success_rate': success_rate,
            'total_bytes_downloaded': self.stats['total_bytes'],
            'average_bytes_per_request': (
                self.stats['total_bytes'] / max(1, self.stats['successful_requests'])
            )
        }

    def test_connection(self) -> bool:
        """Test Firecrawl API connection"""
        try:
            test_url = "https://example.com"
            # Use Firecrawl's scrape method with shorter timeout for test
            result = self.app.scrape(
                test_url,
                formats=['markdown'],
                timeout=30000  # 30 seconds for test
            )

            # Check if we got a valid response
            if result and (hasattr(result, 'markdown') or isinstance(result, dict)):
                self.logger.logger.info("connection_test_successful")
                return True
            else:
                self.logger.logger.error("connection_test_failed", response=str(result))
                return False

        except Exception as e:
            self.logger.logger.error("connection_test_error", error=str(e))
            return False