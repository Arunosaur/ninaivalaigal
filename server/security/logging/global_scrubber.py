"""
Global Log Scrubbing System

Comprehensive secret detection and redaction for logs, telemetry,
and structured data to prevent sensitive information leakage.
"""

import re
import json
import logging
from typing import Any, Dict, List, Pattern, Union, Optional, Callable
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class ScrubPattern:
    """Pattern definition for secret detection."""
    name: str
    pattern: Pattern[str]
    replacement: str
    confidence: float = 1.0


class GlobalLogScrubber:
    """Global scrubber for logs and telemetry data."""
    
    def __init__(self):
        self.patterns: List[ScrubPattern] = []
        self.enabled = True
        self._setup_default_patterns()
    
    def _setup_default_patterns(self):
        """Setup default secret detection patterns."""
        # AWS Access Keys
        self.add_pattern(
            "aws_access_key",
            re.compile(r'AKIA[0-9A-Z]{16}', re.IGNORECASE),
            "[REDACTED_AWS_KEY]"
        )
        
        # Generic API Keys (high entropy alphanumeric)
        self.add_pattern(
            "generic_api_key",
            re.compile(r'[a-zA-Z0-9]{32,}', re.IGNORECASE),
            "[REDACTED_API_KEY]",
            confidence=0.7
        )
        
        # JWT Tokens
        self.add_pattern(
            "jwt_token",
            re.compile(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*'),
            "[REDACTED_JWT]"
        )
        
        # Base64 encoded secrets (high entropy)
        self.add_pattern(
            "base64_secret",
            re.compile(r'[A-Za-z0-9+/]{40,}={0,2}'),
            "[REDACTED_BASE64]",
            confidence=0.6
        )
    
    def add_pattern(self, name: str, pattern: Pattern[str], replacement: str, confidence: float = 1.0):
        """Add a new scrubbing pattern."""
        self.patterns.append(ScrubPattern(name, pattern, replacement, confidence))
    
    def scrub_text(self, text: str) -> str:
        """Scrub secrets from text content."""
        if not self.enabled or not text:
            return text
        
        result = text
        for pattern in self.patterns:
            if pattern.confidence >= 0.8:  # Only apply high-confidence patterns
                result = pattern.pattern.sub(pattern.replacement, result)
        
        return result
    
    def scrub_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively scrub secrets from dictionary data."""
        if not self.enabled:
            return data
        
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.scrub_text(value)
            elif isinstance(value, dict):
                result[key] = self.scrub_dict(value)
            elif isinstance(value, list):
                result[key] = self.scrub_list(value)
            else:
                result[key] = value
        
        return result
    
    def scrub_list(self, data: List[Any]) -> List[Any]:
        """Recursively scrub secrets from list data."""
        if not self.enabled:
            return data
        
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(self.scrub_text(item))
            elif isinstance(item, dict):
                result.append(self.scrub_dict(item))
            elif isinstance(item, list):
                result.append(self.scrub_list(item))
            else:
                result.append(item)
        
        return result
    
    def scrub_json(self, json_str: str) -> str:
        """Scrub secrets from JSON string."""
        if not self.enabled:
            return json_str
        
        try:
            data = json.loads(json_str)
            scrubbed_data = self.scrub_dict(data) if isinstance(data, dict) else self.scrub_list(data)
            return json.dumps(scrubbed_data)
        except (json.JSONDecodeError, TypeError):
            # Fallback to text scrubbing if JSON parsing fails
            return self.scrub_text(json_str)
    
    @contextmanager
    def temporarily_disabled(self):
        """Context manager to temporarily disable scrubbing."""
        old_enabled = self.enabled
        self.enabled = False
        try:
            yield
        finally:
            self.enabled = old_enabled


# Global instance
_global_scrubber = GlobalLogScrubber()


def scrub_text(text: str) -> str:
    """Global function to scrub text."""
    return _global_scrubber.scrub_text(text)


def scrub_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Global function to scrub dictionary."""
    return _global_scrubber.scrub_dict(data)


def scrub_json(json_str: str) -> str:
    """Global function to scrub JSON."""
    return _global_scrubber.scrub_json(json_str)


def add_scrub_pattern(name: str, pattern: Pattern[str], replacement: str, confidence: float = 1.0):
    """Add a pattern to the global scrubber."""
    _global_scrubber.add_pattern(name, pattern, replacement, confidence)


class ScrubberLogHandler(logging.Handler):
    """Log handler that scrubs secrets before logging."""
    
    def __init__(self, target_handler: logging.Handler):
        super().__init__()
        self.target_handler = target_handler
        self.setLevel(target_handler.level)
        self.setFormatter(target_handler.formatter)
    
    def emit(self, record: logging.LogRecord):
        """Emit log record after scrubbing."""
        # Scrub the message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = scrub_text(record.msg)
        
        # Scrub arguments
        if hasattr(record, 'args') and record.args:
            scrubbed_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    scrubbed_args.append(scrub_text(arg))
                elif isinstance(arg, dict):
                    scrubbed_args.append(scrub_dict(arg))
                else:
                    scrubbed_args.append(arg)
            record.args = tuple(scrubbed_args)
        
        self.target_handler.emit(record)


def install_global_scrubber():
    """Install global log scrubbing for all loggers."""
    root_logger = logging.getLogger()
    
    # Wrap existing handlers
    original_handlers = root_logger.handlers[:]
    root_logger.handlers.clear()
    
    for handler in original_handlers:
        scrubber_handler = ScrubberLogHandler(handler)
        root_logger.addHandler(scrubber_handler)


def scrubbing_decorator(func: Callable) -> Callable:
    """Decorator to scrub function return values."""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, str):
            return scrub_text(result)
        elif isinstance(result, dict):
            return scrub_dict(result)
        return result
    return wrapper


# OpenTelemetry integration
def scrub_span_attributes(attributes: Dict[str, Any]) -> Dict[str, Any]:
    """Scrub OpenTelemetry span attributes."""
    return scrub_dict(attributes)


def scrub_telemetry_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Scrub telemetry event data."""
    return scrub_dict(event_data)
