"""
Enhanced Data Validator for Bangladesh Law documents
Performs comprehensive quality checks and validation
"""
import re
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from scrapers.utils.logger import get_logger


class EnhancedDataValidator:
    """Enhanced validator with comprehensive quality checks"""

    def __init__(self):
        self.logger = get_logger("data_validator")

        # Validation rules
        self.min_content_length = 100  # Minimum characters
        self.max_content_length = 10000000  # 10MB max
        self.required_keywords = ['act', 'section', 'law']

        # Legal document patterns
        self.patterns = {
            'act_title': r'(?:ACT|Act)\s+(?:NO|No)?\s*\.?\s*([IVXLCDM]+|\d+)',
            'section': r'(?:Section|SECTION|Sec\.?)\s*(\d+[A-Za-z]?)',
            'chapter': r'(?:CHAPTER|Chapter)\s*([IVXLCDM]+|\d+)',
            'article': r'(?:Article|ARTICLE)\s*(\d+)',
            'subsection': r'\((\d+|[a-z]|[ivx]+)\)',
            'date': r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            'year': r'(?:19|20)\d{2}',
            'ordinance': r'(?:Ordinance|ORDINANCE)\s+(?:No\.?|NO\.?)\s*([IVXLCDM]+|\d+)',
            'amendment': r'(?:Amendment|AMENDMENT|Amended)',
            'repeal': r'(?:Repeal|REPEAL|Repealed)',
            'schedule': r'(?:SCHEDULE|Schedule)\s*(\d+|[IVXLCDM]+)?'
        }

        # Bengali/Bangla language indicators
        self.bengali_patterns = [
            r'[\u0980-\u09FF]',  # Bengali Unicode range
            r'বাংলাদেশ',  # Bangladesh in Bengali
            r'আইন',  # Law in Bengali
            r'ধারা'  # Section in Bengali
        ]

        # Quality metrics thresholds
        self.quality_thresholds = {
            'min_sections': 1,
            'min_words': 50,
            'max_repetition_ratio': 0.8,  # Max 80% repetition
            'min_unique_words': 20
        }

        # Statistics tracking
        self.validation_stats = {
            'total_validated': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }

    def validate_comprehensive(self, content: str, metadata: Dict) -> Tuple[bool, Dict]:
        """
        Perform comprehensive validation with quality scoring

        Returns:
            Tuple of (is_valid, validation_report)
        """
        self.validation_stats['total_validated'] += 1

        report = {
            'timestamp': datetime.now().isoformat(),
            'url': metadata.get('url', 'unknown'),
            'checks': {},
            'quality_score': 0,
            'warnings': [],
            'errors': [],
            'recommendations': []
        }

        # 1. Basic content checks
        if not content:
            report['errors'].append('Empty content')
            self.validation_stats['failed'] += 1
            return False, report

        content_length = len(content)
        report['checks']['content_length'] = content_length

        if content_length < self.min_content_length:
            report['errors'].append(f'Content too short ({content_length} chars)')
            self.validation_stats['failed'] += 1
            return False, report

        if content_length > self.max_content_length:
            report['errors'].append(f'Content too large ({content_length} chars)')
            self.validation_stats['failed'] += 1
            return False, report

        # 2. Language detection
        is_english = self._detect_english(content)
        is_bengali = self._detect_bengali(content)

        report['checks']['language'] = {
            'english': is_english,
            'bengali': is_bengali,
            'mixed': is_english and is_bengali
        }

        if not (is_english or is_bengali):
            report['warnings'].append('No recognized language detected')

        # 3. Legal structure detection
        structure = self._analyze_legal_structure(content)
        report['checks']['legal_structure'] = structure

        if structure['sections'] == 0 and structure['chapters'] == 0:
            report['warnings'].append('No clear legal structure found')

        # 4. Content quality metrics
        quality_metrics = self._calculate_quality_metrics(content)
        report['checks']['quality_metrics'] = quality_metrics

        # Check quality thresholds
        if quality_metrics['unique_words'] < self.quality_thresholds['min_unique_words']:
            report['warnings'].append('Low vocabulary diversity')

        if quality_metrics['repetition_ratio'] > self.quality_thresholds['max_repetition_ratio']:
            report['warnings'].append('High content repetition detected')

        # 5. Metadata validation
        meta_validation = self._validate_metadata(metadata)
        report['checks']['metadata'] = meta_validation

        if not meta_validation['valid']:
            report['warnings'].extend(meta_validation['issues'])

        # 6. Content integrity
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        report['checks']['content_hash'] = content_hash

        if metadata.get('content_hash') and metadata['content_hash'] != content_hash:
            report['errors'].append('Content hash mismatch')

        # 7. Calculate quality score (0-100)
        quality_score = self._calculate_quality_score(report['checks'])
        report['quality_score'] = quality_score

        # 8. Generate recommendations
        if quality_score < 50:
            report['recommendations'].append('Consider manual review of content')

        if structure['sections'] == 0:
            report['recommendations'].append('Parse content for section markers')

        if not is_english and is_bengali:
            report['recommendations'].append('Consider translation for English users')

        # Determine validation result
        is_valid = len(report['errors']) == 0 and quality_score >= 30

        if is_valid:
            self.validation_stats['passed'] += 1
        else:
            self.validation_stats['failed'] += 1

        if len(report['warnings']) > 0:
            self.validation_stats['warnings'] += 1

        # Log validation result
        self.logger.logger.info(
            "validation_complete",
            url=metadata.get('url'),
            valid=is_valid,
            quality_score=quality_score,
            warnings=len(report['warnings']),
            errors=len(report['errors'])
        )

        return is_valid, report

    def _detect_english(self, content: str) -> bool:
        """Detect if content is in English"""
        english_words = ['the', 'and', 'of', 'to', 'in', 'for', 'act', 'section', 'law']
        content_lower = content.lower()
        english_count = sum(1 for word in english_words if word in content_lower)
        return english_count >= 3

    def _detect_bengali(self, content: str) -> bool:
        """Detect if content contains Bengali text"""
        for pattern in self.bengali_patterns:
            if re.search(pattern, content):
                return True
        return False

    def _analyze_legal_structure(self, content: str) -> Dict:
        """Analyze legal document structure"""
        structure = {
            'sections': 0,
            'chapters': 0,
            'articles': 0,
            'schedules': 0,
            'subsections': 0,
            'has_amendments': False,
            'has_repeals': False,
            'act_numbers': [],
            'years_mentioned': []
        }

        # Count sections
        sections = re.findall(self.patterns['section'], content, re.IGNORECASE)
        structure['sections'] = len(set(sections))

        # Count chapters
        chapters = re.findall(self.patterns['chapter'], content, re.IGNORECASE)
        structure['chapters'] = len(set(chapters))

        # Count articles
        articles = re.findall(self.patterns['article'], content, re.IGNORECASE)
        structure['articles'] = len(set(articles))

        # Count schedules
        schedules = re.findall(self.patterns['schedule'], content, re.IGNORECASE)
        structure['schedules'] = len(schedules)

        # Count subsections
        subsections = re.findall(self.patterns['subsection'], content)
        structure['subsections'] = len(subsections)

        # Check for amendments
        if re.search(self.patterns['amendment'], content, re.IGNORECASE):
            structure['has_amendments'] = True

        # Check for repeals
        if re.search(self.patterns['repeal'], content, re.IGNORECASE):
            structure['has_repeals'] = True

        # Extract act numbers
        act_numbers = re.findall(self.patterns['act_title'], content, re.IGNORECASE)
        structure['act_numbers'] = list(set(act_numbers))[:10]  # Limit to 10

        # Extract years
        years = re.findall(self.patterns['year'], content)
        structure['years_mentioned'] = list(set(years))[:10]  # Limit to 10

        return structure

    def _calculate_quality_metrics(self, content: str) -> Dict:
        """Calculate content quality metrics"""
        words = content.lower().split()
        total_words = len(words)
        unique_words = len(set(words))

        # Calculate repetition ratio
        repetition_ratio = 0
        if total_words > 0:
            repetition_ratio = 1 - (unique_words / total_words)

        # Calculate average word length
        avg_word_length = 0
        if total_words > 0:
            avg_word_length = sum(len(word) for word in words) / total_words

        return {
            'total_words': total_words,
            'unique_words': unique_words,
            'repetition_ratio': round(repetition_ratio, 3),
            'avg_word_length': round(avg_word_length, 2),
            'total_lines': content.count('\n'),
            'total_paragraphs': content.count('\n\n')
        }

    def _validate_metadata(self, metadata: Dict) -> Dict:
        """Validate metadata completeness"""
        required_fields = ['url', 'crawled_at', 'content_type']
        issues = []

        for field in required_fields:
            if field not in metadata or not metadata[field]:
                issues.append(f'Missing metadata field: {field}')

        # Validate URL format
        if 'url' in metadata:
            if not metadata['url'].startswith('http'):
                issues.append('Invalid URL format')

        return {
            'valid': len(issues) == 0,
            'issues': issues
        }

    def _calculate_quality_score(self, checks: Dict) -> float:
        """Calculate overall quality score (0-100)"""
        score = 100.0

        # Deduct for missing structure
        structure = checks.get('legal_structure', {})
        if structure.get('sections', 0) == 0:
            score -= 20
        if structure.get('chapters', 0) == 0:
            score -= 10

        # Deduct for quality issues
        metrics = checks.get('quality_metrics', {})
        if metrics.get('total_words', 0) < 50:
            score -= 30
        if metrics.get('unique_words', 0) < 20:
            score -= 20
        if metrics.get('repetition_ratio', 0) > 0.8:
            score -= 15

        # Bonus for good structure
        if structure.get('sections', 0) > 5:
            score += 10
        if structure.get('has_amendments'):
            score += 5

        # Ensure score is within bounds
        return max(0, min(100, score))

    def generate_validation_report(self, output_path: Optional[Path] = None) -> Dict:
        """Generate comprehensive validation report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.validation_stats,
            'success_rate': 0
        }

        if self.validation_stats['total_validated'] > 0:
            report['success_rate'] = round(
                (self.validation_stats['passed'] / self.validation_stats['total_validated']) * 100,
                2
            )

        # Save to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)

            self.logger.logger.info("validation_report_generated", path=str(output_path))

        return report


# For backward compatibility
class DataValidator(EnhancedDataValidator):
    """Backward compatible validator"""

    def is_valid_legal_document(self, content: str, metadata: Dict) -> bool:
        """Simple validation for backward compatibility"""
        is_valid, _ = self.validate_comprehensive(content, metadata)
        return is_valid