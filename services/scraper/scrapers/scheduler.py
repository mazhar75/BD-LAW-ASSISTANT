"""
Scheduler for BD Law Crawler - Manages periodic crawling tasks
"""
import time
import schedule
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.bd_law_crawler import BDLawCrawler
from scrapers.utils.logger import get_logger
from scrapers.config.settings import get_settings

class CrawlerScheduler:
    """
    Manages scheduled crawling tasks for BD law documents
    """

    def __init__(self):
        self.crawler = BDLawCrawler()
        self.logger = get_logger("crawler_scheduler")
        self.settings = get_settings()
        self.is_running = True

    def daily_crawl(self):
        """
        Perform daily crawl of new/updated acts
        """
        self.logger.logger.info("Starting daily crawl...")
        try:
            # Crawl recent acts (last 10)
            self.crawler.crawl_specific_acts(list(range(1, 11)))
            self.logger.logger.info("Daily crawl completed successfully")
        except Exception as e:
            self.logger.logger.error(f"Daily crawl failed: {str(e)}")

    def weekly_full_crawl(self):
        """
        Perform weekly full site crawl
        """
        self.logger.logger.info("Starting weekly full crawl...")
        try:
            self.crawler.crawl_full_site()
            self.logger.logger.info("Weekly full crawl completed successfully")
        except Exception as e:
            self.logger.logger.error(f"Weekly full crawl failed: {str(e)}")

    def check_queue_health(self):
        """
        Check queue health and restart if needed
        """
        try:
            queue_status = self.crawler.queue.get_queue_status()
            self.logger.logger.info(f"Queue status: {queue_status}")

            # If queue has too many failed tasks, attempt retry
            if queue_status.get('failed', 0) > 100:
                self.logger.logger.warning("High number of failed tasks, initiating retry...")
                self.crawler.queue.retry_failed_tasks()

        except Exception as e:
            self.logger.logger.error(f"Queue health check failed: {str(e)}")

    def setup_schedule(self):
        """
        Set up scheduled tasks
        """
        # Daily crawl at 2 AM
        schedule.every().day.at("02:00").do(self.daily_crawl)

        # Weekly full crawl on Sunday at 3 AM
        schedule.every().sunday.at("03:00").do(self.weekly_full_crawl)

        # Queue health check every hour
        schedule.every().hour.do(self.check_queue_health)

        self.logger.logger.info("Scheduler configured:")
        self.logger.logger.info("- Daily crawl at 02:00")
        self.logger.logger.info("- Weekly full crawl on Sunday at 03:00")
        self.logger.logger.info("- Hourly queue health check")

    def run(self):
        """
        Run the scheduler
        """
        self.setup_schedule()
        self.logger.logger.info("Scheduler started")

        # Run initial queue health check
        self.check_queue_health()

        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.logger.logger.info("Scheduler stopped by user")
                self.is_running = False
            except Exception as e:
                self.logger.logger.error(f"Scheduler error: {str(e)}")
                time.sleep(60)  # Wait before retrying

        self.logger.logger.info("Scheduler stopped")

def main():
    """
    Main entry point for the scheduler
    """
    scheduler = CrawlerScheduler()

    # Test connection first
    if not scheduler.crawler.firecrawl.test_connection():
        print("Failed to connect to Firecrawl API. Please check your API key.")
        sys.exit(1)

    print("Starting BD Law Crawler Scheduler...")
    print("Press Ctrl+C to stop")

    scheduler.run()

if __name__ == '__main__':
    main()