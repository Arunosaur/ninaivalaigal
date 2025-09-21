"""
Secret Detection Module

Implements entropy-based and context-aware pattern detection for identifying secrets.
"""

import re
from dataclasses import dataclass
from enum import Enum

from ..utils.entropy import EntropyCalculator


class SecretType(Enum):
    """Types of secrets that can be detected"""
    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    GITHUB_TOKEN = "github_token"
    OPENAI_API_KEY = "openai_api_key"
    JWT_TOKEN = "jwt_token"
    DATABASE_URL = "database_url"
    EMAIL_ADDRESS = "email_address"
    PHONE_NUMBER = "phone_number"
    CREDIT_CARD = "credit_card"
    HIGH_ENTROPY_STRING = "high_entropy_string"
    GENERIC_API_KEY = "generic_api_key"


@dataclass
class SecretMatch:
    """Represents a detected secret"""
    secret_type: SecretType
    start_pos: int
    end_pos: int
    matched_text: str
    confidence: float
    entropy_score: float
    pattern_name: str | None = None
    replacement_text: str = "<REDACTED>"


class EntropyDetector:
    """Entropy-based secret detection"""

    def __init__(self, min_entropy: float = 4.5, min_length: int = 20, max_length: int = 200):
        self.min_entropy = min_entropy
        self.min_length = min_length
        self.max_length = max_length
        self.entropy_calculator = EntropyCalculator()

    def detect_high_entropy_secrets(self, text: str) -> list[SecretMatch]:
        """
        Detect high-entropy strings that may be secrets.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of detected secret matches
        """
        matches = []

        # Split text into potential secret candidates
        candidates = self._extract_candidates(text)

        for candidate, start_pos, end_pos in candidates:
            entropy_metrics = self.entropy_calculator.get_entropy_metrics(candidate)

            if self._is_high_entropy_secret(candidate, entropy_metrics):
                confidence = self._calculate_confidence(entropy_metrics)

                match = SecretMatch(
                    secret_type=SecretType.HIGH_ENTROPY_STRING,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    matched_text=candidate,
                    confidence=confidence,
                    entropy_score=entropy_metrics['shannon_entropy'],
                    replacement_text=f"<REDACTED_HIGH_ENTROPY_{len(candidate)}>"
                )
                matches.append(match)

        return matches

    def _extract_candidates(self, text: str) -> list[tuple[str, int, int]]:
        """Extract potential secret candidates from text"""
        candidates = []

        # Look for continuous alphanumeric + special character sequences
        pattern = r'[A-Za-z0-9+/=_\-\.]{20,200}'

        for match in re.finditer(pattern, text):
            candidate = match.group()
            start_pos = match.start()
            end_pos = match.end()

            # Filter out common non-secrets
            if not self._is_likely_non_secret(candidate):
                candidates.append((candidate, start_pos, end_pos))

        return candidates

    def _is_high_entropy_secret(self, candidate: str, entropy_metrics: dict[str, float]) -> bool:
        """Check if candidate is likely a high-entropy secret"""
        return (
            len(candidate) >= self.min_length and
            len(candidate) <= self.max_length and
            entropy_metrics['shannon_entropy'] >= self.min_entropy and
            entropy_metrics['char_diversity'] > 0.6  # Good character diversity
        )

    def _is_likely_non_secret(self, candidate: str) -> bool:
        """Check if candidate is likely not a secret"""
        # Common non-secret patterns
        non_secret_patterns = [
            r'^[0-9]+$',  # Pure numbers
            r'^[A-Za-z]+$',  # Pure letters
            r'.*\.(com|org|net|edu|gov).*',  # Domain names
            r'^https?://',  # URLs
            r'^\d{4}-\d{2}-\d{2}',  # Dates
        ]

        for pattern in non_secret_patterns:
            if re.match(pattern, candidate):
                return True

        return False

    def _calculate_confidence(self, entropy_metrics: dict[str, float]) -> float:
        """Calculate confidence score for entropy-based detection"""
        entropy = entropy_metrics['shannon_entropy']
        diversity = entropy_metrics['char_diversity']
        length = entropy_metrics['length']

        # Base confidence from entropy
        confidence = min(entropy / 6.0, 1.0)  # Normalize to 0-1

        # Boost for good character diversity
        confidence *= (0.5 + 0.5 * diversity)

        # Boost for appropriate length
        if 30 <= length <= 100:
            confidence *= 1.1
        elif length > 100:
            confidence *= 0.9

        return min(confidence, 1.0)


class ContextAwareDetector:
    """Context-aware pattern detection for provider-specific secrets"""

    PROVIDER_PATTERNS = {
        SecretType.AWS_ACCESS_KEY: {
            'pattern': r'AKIA[0-9A-Z]{16}',
            'confidence': 0.95,
            'replacement': '<REDACTED_AWS_ACCESS_KEY>'
        },
        SecretType.AWS_SECRET_KEY: {
            'pattern': r'[A-Za-z0-9/+=]{40}',
            'confidence': 0.8,
            'replacement': '<REDACTED_AWS_SECRET_KEY>',
            'context_required': ['aws', 'secret', 'key']
        },
        SecretType.GITHUB_TOKEN: {
            'pattern': r'ghp_[a-zA-Z0-9]{36}',
            'confidence': 0.95,
            'replacement': '<REDACTED_GITHUB_TOKEN>'
        },
        SecretType.OPENAI_API_KEY: {
            'pattern': r'sk-[a-zA-Z0-9]{20,}',
            'confidence': 0.95,
            'replacement': '<REDACTED_OPENAI_API_KEY>'
        },
        SecretType.JWT_TOKEN: {
            'pattern': r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
            'confidence': 0.9,
            'replacement': '<REDACTED_JWT_TOKEN>'
        },
        SecretType.DATABASE_URL: {
            'pattern': r'postgresql://[^:]+:[^@]+@[^/]+/\w+',
            'confidence': 0.95,
            'replacement': '<REDACTED_DATABASE_URL>'
        },
        SecretType.EMAIL_ADDRESS: {
            'pattern': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'confidence': 0.85,
            'replacement': '<REDACTED_EMAIL>'
        },
        SecretType.PHONE_NUMBER: {
            'pattern': r'(\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
            'confidence': 0.8,
            'replacement': '<REDACTED_PHONE>'
        },
        SecretType.CREDIT_CARD: {
            'pattern': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            'confidence': 0.9,
            'replacement': '<REDACTED_CREDIT_CARD>'
        },
        SecretType.GENERIC_API_KEY: {
            'pattern': r'[Aa][Pp][Ii][-_]?[Kk][Ee][Yy][\s]*[:=][\s]*["\']?([A-Za-z0-9_\-]{20,})["\']?',
            'confidence': 0.7,
            'replacement': '<REDACTED_API_KEY>'
        }
    }

    def __init__(self):
        self.compiled_patterns = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        for secret_type, config in self.PROVIDER_PATTERNS.items():
            self.compiled_patterns[secret_type] = re.compile(config['pattern'], re.IGNORECASE)

    def detect_secrets(self, text: str) -> list[SecretMatch]:
        """
        Detect secrets using provider-specific patterns.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of detected secret matches
        """
        matches = []

        for secret_type, pattern in self.compiled_patterns.items():
            config = self.PROVIDER_PATTERNS[secret_type]

            for match in pattern.finditer(text):
                # Check context requirements if specified
                if 'context_required' in config:
                    if not self._check_context_requirements(text, match, config['context_required']):
                        continue

                secret_match = SecretMatch(
                    secret_type=secret_type,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    matched_text=match.group(),
                    confidence=config['confidence'],
                    entropy_score=EntropyCalculator.calculate_shannon_entropy(match.group()),
                    pattern_name=secret_type.value,
                    replacement_text=config['replacement']
                )
                matches.append(secret_match)

        return matches

    def _check_context_requirements(self, text: str, match: re.Match, required_context: list[str]) -> bool:
        """Check if required context words are present near the match"""
        # Look for context words within 50 characters before and after the match
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context_window = text[start:end].lower()

        return any(context_word in context_window for context_word in required_context)


class CombinedSecretDetector:
    """Combined detector using both entropy and pattern-based detection"""

    def __init__(self, min_entropy: float = 4.5, min_length: int = 20):
        self.entropy_detector = EntropyDetector(min_entropy, min_length)
        self.pattern_detector = ContextAwareDetector()

    def detect_all_secrets(self, text: str) -> list[SecretMatch]:
        """
        Detect secrets using both entropy and pattern-based methods.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Deduplicated list of detected secret matches
        """
        # Get matches from both detectors
        pattern_matches = self.pattern_detector.detect_secrets(text)
        entropy_matches = self.entropy_detector.detect_high_entropy_secrets(text)

        # Combine and deduplicate matches
        all_matches = pattern_matches + entropy_matches
        deduplicated_matches = self._deduplicate_matches(all_matches)

        # Sort by position
        deduplicated_matches.sort(key=lambda m: m.start_pos)

        return deduplicated_matches

    def _deduplicate_matches(self, matches: list[SecretMatch]) -> list[SecretMatch]:
        """Remove overlapping matches, keeping the highest confidence one"""
        if not matches:
            return []

        # Sort by confidence (descending) then by position
        matches.sort(key=lambda m: (-m.confidence, m.start_pos))

        deduplicated = []
        for match in matches:
            # Check if this match overlaps with any existing match
            overlaps = False
            for existing in deduplicated:
                if self._matches_overlap(match, existing):
                    overlaps = True
                    break

            if not overlaps:
                deduplicated.append(match)

        return deduplicated

    def _matches_overlap(self, match1: SecretMatch, match2: SecretMatch) -> bool:
        """Check if two matches overlap"""
        return not (match1.end_pos <= match2.start_pos or match2.end_pos <= match1.start_pos)
