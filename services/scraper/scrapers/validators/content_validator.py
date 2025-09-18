"""
Content validation for scraped legal documents
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from bs4 import BeautifulSoup
import hashlib

from scrapers.utils.logger import get_logger


class ValidationLevel(Enum):
    """Validation severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Validation result container"""
    is_valid: bool
    issues: List[Dict[str, any]]
    metadata: Dict[str, any]
    content_type: str
    language: str

    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return any(issue['level'] == ValidationLevel.ERROR.value for issue in self.issues)


class LegalDocumentValidator:
    """
    Validator for Bangladesh legal documents
    """

    def __init__(self):
        self.logger = get_logger("validator")

        # Patterns for different document types
        self.act_pattern = re.compile(r'(Act\s+(No\.\s*)?\d+\s+of\s+\d{4})', re.IGNORECASE)
        self.section_pattern = re.compile(r'(Section|ধারা)\s*\d+', re.IGNORECASE)
        self.chapter_pattern = re.compile(r'(Chapter|অধ্যায়)\s+[IVX\d]+', re.IGNORECASE)

        # Bengali text pattern
        self.bengali_pattern = re.compile(r'[\u0980-\u09FF]+')

        # Minimum content requirements
        self.min_content_length = 100
        self.min_sections = 1

    def validate(self, url: str, content: str, html: str = None) -> ValidationResult:
        """
        Validate scraped content

        Args:
            url: Source URL
            content: Markdown content
            html: HTML content

        Returns:
            ValidationResult object
        """
        issues = []
        metadata = {}

        # Basic content validation
        if not content or len(content.strip()) < self.min_content_length:
            issues.append({
                'level': ValidationLevel.ERROR.value,
                'message': f'Content too short ({len(content)} chars)',
                'field': 'content'
            })

        # Detect document type
        content_type = self._detect_content_type(url, content)
        metadata['content_type'] = content_type

        # Detect language
        language = self._detect_language(content)
        metadata['language'] = language

        # Validate based on content type
        if content_type == 'act':
            act_issues, act_metadata = self._validate_act(content, html)
            issues.extend(act_issues)
            metadata.update(act_metadata)
        elif content_type == 'volume':
            volume_issues, volume_metadata = self._validate_volume(content, html)
            issues.extend(volume_issues)
            metadata.update(volume_metadata)

        # Check for common issues
        common_issues = self._check_common_issues(content, html)
        issues.extend(common_issues)

        # Calculate content hash for deduplication
        metadata['content_hash'] = hashlib.sha256(content.encode()).hexdigest()

        # Determine overall validity
        is_valid = not any(issue['level'] == ValidationLevel.ERROR.value for issue in issues)

        result = ValidationResult(
            is_valid=is_valid,
            issues=issues,
            metadata=metadata,
            content_type=content_type,
            language=language
        )

        self.logger.log_validation(url, is_valid, issues)

        return result

    def _detect_content_type(self, url: str, content: str) -> str:
        """Detect type of legal document"""
        url_lower = url.lower()

        if '/act-' in url_lower or self.act_pattern.search(content):
            return 'act'
        elif '/volume-' in url_lower:
            return 'volume'
        elif '/regulation' in url_lower:
            return 'regulation'
        elif '/ordinance' in url_lower:
            return 'ordinance'
        elif 'index' in url_lower or 'list' in url_lower:
            return 'index'
        else:
            return 'unknown'

    def _detect_language(self, content: str) -> str:
        """Detect primary language of content"""
        bengali_chars = len(self.bengali_pattern.findall(content))
        total_chars = len(content)

        if total_chars == 0:
            return 'unknown'

        bengali_ratio = bengali_chars / total_chars

        if bengali_ratio > 0.3:
            return 'bengali'
        else:
            return 'english'

    def _validate_act(self, content: str, html: str = None) -> Tuple[List[Dict], Dict]:
        """Validate act document"""
        issues = []
        metadata = {}

        # Extract act information
        act_match = self.act_pattern.search(content)
        if act_match:
            metadata['act_title'] = act_match.group(0)
        else:
            issues.append({
                'level': ValidationLevel.WARNING.value,
                'message': 'Could not extract act title',
                'field': 'act_title'
            })

        # Check for sections
        sections = self.section_pattern.findall(content)
        metadata['section_count'] = len(sections)

        if len(sections) < self.min_sections:
            issues.append({
                'level': ValidationLevel.WARNING.value,
                'message': f'Too few sections found ({len(sections)})',
                'field': 'sections'
            })

        # Check for chapters
        chapters = self.chapter_pattern.findall(content)
        metadata['chapter_count'] = len(chapters)

        # Validate structure
        if html:
            soup = BeautifulSoup(html, 'html.parser')

            # Check for proper heading structure
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
            if len(headings) < 2:
                issues.append({
                    'level': ValidationLevel.INFO.value,
                    'message': 'Document lacks proper heading structure',
                    'field': 'structure'
                })

        return issues, metadata

    def _validate_volume(self, content: str, html: str = None) -> Tuple[List[Dict], Dict]:
        """Validate volume/index document"""
        issues = []
        metadata = {}

        # Check for act links
        act_links = re.findall(r'/act-\d+\.html', content)
        metadata['act_count'] = len(act_links)

        if len(act_links) == 0:
            issues.append({
                'level': ValidationLevel.WARNING.value,
                'message': 'No act links found in volume page',
                'field': 'links'
            })

        return issues, metadata

    def _check_common_issues(self, content: str, html: str = None) -> List[Dict]:
        """Check for common content issues"""
        issues = []

        # Check for encoding issues
        if '�' in content or '\ufffd' in content:
            issues.append({
                'level': ValidationLevel.WARNING.value,
                'message': 'Content contains encoding errors',
                'field': 'encoding'
            })

        # Check for excessive whitespace
        if '\n\n\n\n' in content:
            issues.append({
                'level': ValidationLevel.INFO.value,
                'message': 'Content contains excessive whitespace',
                'field': 'formatting'
            })

        # Check for truncated content
        if content.endswith('...') or content.endswith('…'):
            issues.append({
                'level': ValidationLevel.WARNING.value,
                'message': 'Content appears to be truncated',
                'field': 'completeness'
            })

        # Check for missing Bengali fonts
        if self.bengali_pattern.search(content) and html:
            soup = BeautifulSoup(html, 'html.parser')
            if not soup.find(attrs={'lang': re.compile('bn|bengali', re.I)}):
                issues.append({
                    'level': ValidationLevel.INFO.value,
                    'message': 'Bengali content lacks proper language tags',
                    'field': 'i18n'
                })

        return issues

    def validate_batch(self, items: List[Dict]) -> List[ValidationResult]:
        """Validate multiple documents"""
        results = []

        for item in items:
            result = self.validate(
                url=item.get('url', ''),
                content=item.get('content', ''),
                html=item.get('html', '')
            )
            results.append(result)

        # Log summary
        valid_count = sum(1 for r in results if r.is_valid)
        self.logger.logger.info(
            "batch_validation_complete",
            total=len(results),
            valid=valid_count,
            invalid=len(results) - valid_count
        )

        return results