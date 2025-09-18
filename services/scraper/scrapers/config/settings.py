"""
Configuration management using Pydantic for type safety and validation
"""
from typing import Optional, Dict, Any
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Main settings using environment variables directly"""

    def __init__(self):
        # Firecrawl settings
        self.firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY', 'fc-3b27f7cc5dec461cba61a71d5946d73b')
        self.firecrawl_base_url = os.getenv('FIRECRAWL_BASE_URL', 'https://api.firecrawl.dev')
        self.firecrawl_timeout = int(os.getenv('CRAWLER_TIMEOUT', '600000'))
        self.firecrawl_max_retries = int(os.getenv('CRAWLER_MAX_RETRIES', '3'))

        # Redis settings
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6380'))
        self.redis_db = int(os.getenv('REDIS_DB', '0'))
        self.redis_password = os.getenv('REDIS_PASSWORD', None)

        # Database settings
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:nihad1086@localhost:5432/bdlaw')
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = int(os.getenv('DB_PORT', '5432'))
        self.db_name = os.getenv('DB_NAME', 'bdlaw')
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD', 'nihad1086')

        # Crawler settings
        self.crawler_batch_size = int(os.getenv('CRAWLER_BATCH_SIZE', '50'))
        self.crawler_max_depth = int(os.getenv('CRAWLER_MAX_DEPTH', '4'))
        self.crawler_rate_limit = float(os.getenv('CRAWLER_RATE_LIMIT', '2.0'))
        self.crawler_base_url = 'http://bdlaws.minlaw.gov.bd'
        self.crawler_laws_index_url = 'http://bdlaws.minlaw.gov.bd/laws-of-bangladesh.html'

        # Storage settings
        self.data_dir = Path(os.getenv('DATA_DIR', './data'))
        self.raw_data_dir = Path(os.getenv('RAW_DATA_DIR', './data/raw'))
        self.processed_data_dir = Path(os.getenv('PROCESSED_DATA_DIR', './data/processed'))
        self.log_dir = Path(os.getenv('LOG_DIR', './data/logs'))

        # Create directories
        for dir_path in [self.data_dir, self.raw_data_dir, self.processed_data_dir, self.log_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Monitoring settings
        self.sentry_dsn = os.getenv('SENTRY_DSN', None)
        self.prometheus_port = int(os.getenv('PROMETHEUS_PORT', '9090'))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = os.getenv('DEBUG', 'True').lower() == 'true'

        # Create sub-objects for compatibility
        self.firecrawl = type('obj', (object,), {
            'api_key': self.firecrawl_api_key,
            'base_url': self.firecrawl_base_url,
            'timeout': self.firecrawl_timeout,
            'max_retries': self.firecrawl_max_retries
        })()

        self.redis = type('obj', (object,), {
            'host': self.redis_host,
            'port': self.redis_port,
            'db': self.redis_db,
            'password': self.redis_password,
            'url': f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
        })()

        self.database = type('obj', (object,), {
            'url': self.database_url,
            'host': self.db_host,
            'port': self.db_port,
            'name': self.db_name,
            'user': self.db_user,
            'password': self.db_password,
            'connection_url': self.database_url or f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        })()

        self.crawler = type('obj', (object,), {
            'batch_size': self.crawler_batch_size,
            'max_depth': self.crawler_max_depth,
            'rate_limit': self.crawler_rate_limit,
            'base_url': self.crawler_base_url,
            'laws_index_url': self.crawler_laws_index_url,
            'include_patterns': [
                '/volume-*.html',
                '/act-*.html',
                '/act-details-*.html',
                '/act_sections.php*',
                '/bangla_*',
                '/print_*'
            ],
            'exclude_patterns': [
                '*.pdf',
                '/download/*',
                '/admin/*',
                '*.doc',
                '*.docx'
            ]
        })()

        self.storage = type('obj', (object,), {
            'data_dir': self.data_dir,
            'raw_data_dir': self.raw_data_dir,
            'processed_data_dir': self.processed_data_dir,
            'log_dir': self.log_dir,
            'get_subdirs': self._get_subdirs
        })()

        self.monitoring = type('obj', (object,), {
            'sentry_dsn': self.sentry_dsn,
            'prometheus_port': self.prometheus_port,
            'log_level': self.log_level,
            'environment': self.environment,
            'debug': self.debug
        })()

    def _get_subdirs(self) -> Dict[str, Path]:
        """Get all subdirectories"""
        subdirs = {
            'volumes': self.raw_data_dir / 'volumes',
            'acts': self.raw_data_dir / 'acts',
            'bengali': self.raw_data_dir / 'bengali',
            'metadata': self.processed_data_dir / 'metadata',
            'chunks': self.processed_data_dir / 'chunks',
        }

        # Create subdirectories
        for subdir in subdirs.values():
            subdir.mkdir(parents=True, exist_ok=True)

        return subdirs


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Export for convenience
settings = get_settings()