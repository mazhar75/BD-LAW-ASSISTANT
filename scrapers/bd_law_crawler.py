"""
Main BD Law Crawler - Orchestrates the complete scraping pipeline
"""
import asyncio
import time
from typing import List, Dict, Optional
from datetime import datetime
import click
import sys
from pathlib import Path
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.core.firecrawl_client import FirecrawlClient, CrawlResult
from scrapers.core.queue_manager import RedisQueueManager, QueuePriority, QueueTask
from scrapers.validators.content_validator import LegalDocumentValidator
from scrapers.storage.file_storage import DocumentStorage
from scrapers.config.settings import get_settings
from scrapers.utils.logger import get_logger


class BDLawCrawler:
    """
    Main crawler orchestrator for Bangladesh law documents
    """

    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("bd_law_crawler")

        # Initialize components
        self.firecrawl = FirecrawlClient()
        self.queue = RedisQueueManager("bdlaw_scraper")
        self.validator = LegalDocumentValidator()
        self.storage = DocumentStorage()

        # Crawler state
        self.is_running = False
        self.start_time = None
        self.stats = {
            'urls_queued': 0,
            'urls_processed': 0,
            'urls_failed': 0,
            'validation_passed': 0,
            'validation_failed': 0,
            'storage_success': 0,
            'storage_failed': 0
        }

    def discover_urls(self) -> List[str]:
        """
        Discover all URLs to crawl from the main index
        """
        self.logger.logger.info("Starting URL discovery...")

        urls_to_crawl = []

        # Start with the main laws page
        main_url = self.settings.crawler.laws_index_url

        try:
            # Scrape the main index page
            index_result = self.firecrawl.scrape_url(main_url)

            if index_result.success:
                # Extract volume links (volume-1.html to volume-51.html)
                volume_pattern = re.compile(r'href="(/volume-\d+\.html)"')
                volume_links = volume_pattern.findall(index_result.html)

                for link in volume_links:
                    full_url = self.settings.crawler.base_url + link
                    urls_to_crawl.append(full_url)
                    self.logger.logger.info(f"Found volume: {full_url}")

                # Extract act links (act-1.html to act-1242.html+)
                act_pattern = re.compile(r'href="(/act-\d+\.html)"')
                act_links = act_pattern.findall(index_result.html)

                for link in act_links:
                    full_url = self.settings.crawler.base_url + link
                    urls_to_crawl.append(full_url)

                # Store the index page itself
                self.storage.store_document(index_result, {'content_type': 'index', 'language': 'english'})

            self.logger.logger.info(f"Discovered {len(urls_to_crawl)} URLs to crawl")

        except Exception as e:
            self.logger.logger.error(f"URL discovery failed: {str(e)}")

        return urls_to_crawl

    def queue_urls(self, urls: List[str], priority: QueuePriority = QueuePriority.NORMAL):
        """
        Add URLs to the processing queue
        """
        # Separate volumes and acts for prioritization
        volume_urls = [url for url in urls if '/volume-' in url]
        act_urls = [url for url in urls if '/act-' in url]

        # Queue volumes with higher priority (they contain more act links)
        for url in volume_urls:
            self.queue.enqueue(url, task_type="crawl_volume", priority=QueuePriority.HIGH)
            self.stats['urls_queued'] += 1

        # Queue acts with normal priority
        for url in act_urls:
            self.queue.enqueue(url, task_type="crawl_act", priority=QueuePriority.NORMAL)
            self.stats['urls_queued'] += 1

        self.logger.logger.info(
            f"Queued {len(volume_urls)} volumes and {len(act_urls)} acts"
        )

    def process_task(self, task: QueueTask) -> bool:
        """
        Process a single crawl task

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.logger.info(f"Processing: {task.url}")

            # Scrape the URL
            result = self.firecrawl.scrape_url(task.url)

            if not result.success:
                self.stats['urls_failed'] += 1
                self.queue.mark_failed(task.id, result.error)
                return False

            # Validate content
            validation = self.validator.validate(
                url=result.url,
                content=result.content,
                html=result.html
            )

            if validation.is_valid:
                self.stats['validation_passed'] += 1
            else:
                self.stats['validation_failed'] += 1

            # Store document regardless of validation (with validation results)
            try:
                file_path, file_size = self.storage.store_document(
                    result,
                    validation.metadata,
                    compress=True
                )

                if file_path:
                    self.stats['storage_success'] += 1
                    self.logger.logger.info(
                        f"Stored: {file_path} ({file_size / 1024:.2f} KB)"
                    )

                    # If this is a volume page, extract and queue act links
                    if task.type == "crawl_volume":
                        self._extract_and_queue_acts(result)

            except Exception as e:
                self.stats['storage_failed'] += 1
                self.logger.logger.error(f"Storage failed: {str(e)}")
                self.queue.mark_failed(task.id, str(e))
                return False

            # Mark task as completed
            self.queue.mark_completed(task.id, {
                'file_path': file_path,
                'file_size': file_size,
                'validation': validation.metadata
            })

            self.stats['urls_processed'] += 1
            return True

        except Exception as e:
            self.logger.logger.error(f"Task processing failed: {str(e)}")
            self.queue.mark_failed(task.id, str(e))
            return False

    def _extract_and_queue_acts(self, volume_result: CrawlResult):
        """
        Extract act links from a volume page and queue them
        """
        act_pattern = re.compile(r'href="(/act-\d+\.html)"')
        act_links = act_pattern.findall(volume_result.html)

        new_acts = []
        for link in act_links:
            full_url = self.settings.crawler.base_url + link
            # Queue with lower priority since volumes are already being processed
            task_id = self.queue.enqueue(
                full_url,
                task_type="crawl_act",
                priority=QueuePriority.LOW
            )
            if task_id:
                new_acts.append(full_url)

        if new_acts:
            self.logger.logger.info(
                f"Queued {len(new_acts)} new acts from volume"
            )
            self.stats['urls_queued'] += len(new_acts)

    def run_worker(self, max_tasks: Optional[int] = None):
        """
        Run crawler worker that processes tasks from queue

        Args:
            max_tasks: Maximum number of tasks to process (None for unlimited)
        """
        self.is_running = True
        self.start_time = datetime.now()
        tasks_processed = 0

        self.logger.logger.info("Crawler worker started")

        try:
            while self.is_running:
                # Check max_tasks limit
                if max_tasks and tasks_processed >= max_tasks:
                    self.logger.logger.info(f"Reached max_tasks limit ({max_tasks})")
                    break

                # Get next task from queue
                task = self.queue.dequeue(timeout=5)

                if task is None:
                    # No tasks available
                    queue_status = self.queue.get_queue_status()
                    if queue_status['pending'] == 0:
                        self.logger.logger.info("Queue empty, waiting for tasks...")
                        time.sleep(10)
                        continue
                else:
                    # Process the task
                    success = self.process_task(task)
                    tasks_processed += 1

                    # Log progress
                    if tasks_processed % 10 == 0:
                        self._log_progress()

        except KeyboardInterrupt:
            self.logger.logger.info("Crawler interrupted by user")
        except Exception as e:
            self.logger.logger.error(f"Crawler error: {str(e)}")
        finally:
            self.is_running = False
            self._log_final_stats()

    def crawl_full_site(self):
        """
        Perform full site crawl
        """
        self.logger.logger.info("Starting full site crawl")

        # Discover all URLs
        urls = self.discover_urls()

        if not urls:
            self.logger.logger.error("No URLs discovered")
            return

        # Queue all URLs
        self.queue_urls(urls)

        # Start processing
        self.run_worker()

    def crawl_specific_acts(self, act_numbers: List[int]):
        """
        Crawl specific act numbers
        """
        urls = [f"{self.settings.crawler.base_url}/act-{num}.html" for num in act_numbers]
        self.queue_urls(urls, priority=QueuePriority.HIGH)
        self.run_worker(max_tasks=len(urls))

    def crawl_volumes(self, volume_numbers: List[int] = None):
        """
        Crawl specific volumes or all volumes
        """
        if volume_numbers:
            urls = [f"{self.settings.crawler.base_url}/volume-{num}.html" for num in volume_numbers]
        else:
            # Crawl all 51 volumes
            urls = [f"{self.settings.crawler.base_url}/volume-{num}.html" for num in range(1, 52)]

        self.queue_urls(urls, priority=QueuePriority.HIGH)
        self.run_worker()

    def _log_progress(self):
        """Log current progress"""
        runtime = (datetime.now() - self.start_time).total_seconds()
        rate = self.stats['urls_processed'] / max(1, runtime / 60)  # URLs per minute

        queue_status = self.queue.get_queue_status()

        self.logger.logger.info(
            f"Progress: Processed={self.stats['urls_processed']}, "
            f"Failed={self.stats['urls_failed']}, "
            f"Pending={queue_status['pending']}, "
            f"Rate={rate:.1f} URLs/min"
        )

    def _log_final_stats(self):
        """Log final statistics"""
        runtime = (datetime.now() - self.start_time).total_seconds()

        # Get storage stats
        storage_stats = self.storage.get_storage_stats()

        # Get Firecrawl stats
        firecrawl_stats = self.firecrawl.get_statistics()

        self.logger.logger.info("=" * 50)
        self.logger.logger.info("CRAWL COMPLETE - Final Statistics")
        self.logger.logger.info("=" * 50)
        self.logger.logger.info(f"Runtime: {runtime / 60:.2f} minutes")
        self.logger.logger.info(f"URLs Queued: {self.stats['urls_queued']}")
        self.logger.logger.info(f"URLs Processed: {self.stats['urls_processed']}")
        self.logger.logger.info(f"URLs Failed: {self.stats['urls_failed']}")
        self.logger.logger.info(f"Validation Passed: {self.stats['validation_passed']}")
        self.logger.logger.info(f"Validation Failed: {self.stats['validation_failed']}")
        self.logger.logger.info(f"Documents Stored: {storage_stats['files_stored']}")
        self.logger.logger.info(f"Duplicates Skipped: {storage_stats['duplicates_skipped']}")
        self.logger.logger.info(f"Total Size: {storage_stats['total_size_mb']:.2f} MB")
        self.logger.logger.info(f"Success Rate: {firecrawl_stats['success_rate'] * 100:.1f}%")
        self.logger.logger.info("=" * 50)

        # Save metrics
        self.logger.save_metrics()


@click.command()
@click.option('--mode', type=click.Choice(['full', 'volumes', 'acts', 'worker']),
              default='worker', help='Crawl mode')
@click.option('--volumes', '-v', multiple=True, type=int, help='Specific volume numbers')
@click.option('--acts', '-a', multiple=True, type=int, help='Specific act numbers')
@click.option('--max-tasks', '-m', type=int, help='Maximum tasks to process')
@click.option('--test', is_flag=True, help='Test mode - crawl only 5 URLs')
def main(mode, volumes, acts, max_tasks, test):
    """
    BD Law Crawler - Scrape Bangladesh legal documents
    """
    crawler = BDLawCrawler()

    # Test Firecrawl connection first
    if not crawler.firecrawl.test_connection():
        click.echo("Failed to connect to Firecrawl API. Please check your API key.")
        sys.exit(1)

    click.echo(f"Starting BD Law Crawler in {mode} mode...")

    if test:
        click.echo("TEST MODE: Crawling first 5 acts only")
        crawler.crawl_specific_acts(list(range(1, 6)))
    elif mode == 'full':
        crawler.crawl_full_site()
    elif mode == 'volumes':
        if volumes:
            crawler.crawl_volumes(list(volumes))
        else:
            crawler.crawl_volumes()  # All volumes
    elif mode == 'acts':
        if acts:
            crawler.crawl_specific_acts(list(acts))
        else:
            click.echo("Please specify act numbers with --acts")
    elif mode == 'worker':
        # Just run as a worker processing existing queue
        crawler.run_worker(max_tasks=max_tasks)


if __name__ == '__main__':
    main()