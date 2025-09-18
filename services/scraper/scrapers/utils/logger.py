"""
Structured logging configuration for the scraping system
"""
import structlog
import logging
import sys
from pathlib import Path
from typing import Any, Dict
from datetime import datetime
import json


def setup_logging(log_level: str = "INFO", log_dir: Path = None) -> structlog.BoundLogger:
    """
    Configure structured logging with file and console output
    """
    # Create log directory
    if log_dir is None:
        log_dir = Path("./data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure Python's logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            structlog.processors.dict_tracebacks,
            structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


class ScraperLogger:
    """
    Specialized logger for scraping operations
    """

    def __init__(self, name: str = "scraper", log_dir: Path = None):
        self.name = name
        self.log_dir = log_dir or Path("./data/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup structured logger
        self.logger = setup_logging(log_dir=self.log_dir)
        self.logger = self.logger.bind(component=name)

        # Create JSON file logger for metrics
        self.metrics_file = self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
        self.stats = {
            "started_at": datetime.now().isoformat(),
            "pages_scraped": 0,
            "pages_failed": 0,
            "errors": []
        }

    def log_scrape_start(self, url: str, **kwargs):
        """Log start of scraping operation"""
        self.logger.info("scrape_started", url=url, **kwargs)

    def log_scrape_success(self, url: str, size: int = 0, duration: float = 0, **kwargs):
        """Log successful scrape"""
        self.stats["pages_scraped"] += 1
        self.logger.info(
            "scrape_success",
            url=url,
            size_bytes=size,
            duration_seconds=duration,
            total_scraped=self.stats["pages_scraped"],
            **kwargs
        )

    def log_scrape_error(self, url: str, error: Exception, **kwargs):
        """Log scraping error"""
        self.stats["pages_failed"] += 1
        self.stats["errors"].append({
            "url": url,
            "error": str(error),
            "timestamp": datetime.now().isoformat()
        })

        self.logger.error(
            "scrape_failed",
            url=url,
            error=str(error),
            error_type=type(error).__name__,
            total_failed=self.stats["pages_failed"],
            **kwargs
        )

    def log_queue_status(self, queue_size: int, processed: int, **kwargs):
        """Log queue status"""
        self.logger.info(
            "queue_status",
            queue_size=queue_size,
            processed=processed,
            pending=queue_size - processed,
            **kwargs
        )

    def log_rate_limit(self, wait_time: float, **kwargs):
        """Log rate limiting"""
        self.logger.warning(
            "rate_limited",
            wait_seconds=wait_time,
            **kwargs
        )

    def log_validation(self, url: str, valid: bool, issues: list = None, **kwargs):
        """Log content validation results"""
        if valid:
            self.logger.info("validation_passed", url=url, **kwargs)
        else:
            self.logger.warning(
                "validation_failed",
                url=url,
                issues=issues or [],
                **kwargs
            )

    def log_storage(self, file_path: str, size: int, **kwargs):
        """Log file storage operation"""
        self.logger.info(
            "file_stored",
            path=file_path,
            size_bytes=size,
            **kwargs
        )

    def save_metrics(self):
        """Save metrics to JSON file"""
        self.stats["ended_at"] = datetime.now().isoformat()
        self.stats["success_rate"] = (
            self.stats["pages_scraped"] /
            max(1, self.stats["pages_scraped"] + self.stats["pages_failed"])
        )

        with open(self.metrics_file, 'w') as f:
            json.dump(self.stats, f, indent=2)

        self.logger.info(
            "metrics_saved",
            file=str(self.metrics_file),
            total_scraped=self.stats["pages_scraped"],
            total_failed=self.stats["pages_failed"],
            success_rate=self.stats["success_rate"]
        )

    def get_child(self, name: str) -> 'ScraperLogger':
        """Create a child logger with inherited context"""
        child = ScraperLogger(f"{self.name}.{name}", self.log_dir)
        child.logger = self.logger.bind(subcomponent=name)
        return child


# Global logger instance
_logger: ScraperLogger = None


def get_logger(name: str = "scraper") -> ScraperLogger:
    """Get or create logger instance"""
    global _logger
    if _logger is None:
        _logger = ScraperLogger(name)
    return _logger