"""
Detector glue system that provides a unified interface for the redaction engine.
Attempts to import and use the existing redaction engine, falls back to basic detectors.
"""
from __future__ import annotations
import typing as t
import re
from typing import Optional

def detector_fn(text: str) -> str:
    """
    A glue function that tries to import and call your existing
    server.security.redaction.engine.redact(); if that's not available,
    it falls back to sensible regex detectors (AWS, GitHub, Slack, JWT, PEM).
    """
    try:
        # Try to use existing redaction engine
        from server.security.redaction import RedactionEngine
        from server.security.redaction.config import ContextSensitivity
        
        engine = RedactionEngine()
        result = engine.redact(text, ContextSensitivity.CONFIDENTIAL)
        return result.redacted_text
    except ImportError:
        # Fallback to basic regex patterns
        return _fallback_redaction(text)

def _fallback_redaction(text: str) -> str:
    """Fallback redaction using basic regex patterns"""
    patterns = [
        # AWS Access Keys
        (r'AKIA[0-9A-Z]{16}', '[REDACTED-AWS-KEY]'),
        # GitHub Personal Access Tokens  
        (r'ghp_[A-Za-z0-9]{36}', '[REDACTED-GITHUB-TOKEN]'),
        # OpenAI API Keys
        (r'sk-[A-Za-z0-9]{48}', '[REDACTED-OPENAI-KEY]'),
        # Slack Bot Tokens
        (r'xoxb-[0-9]+-[0-9]+-[A-Za-z0-9]+', '[REDACTED-SLACK-TOKEN]'),
        # JWT Tokens (basic pattern)
        (r'eyJ[A-Za-z0-9+/=]+\.eyJ[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=_-]+', '[REDACTED-JWT]'),
        # PEM Keys
        (r'-----BEGIN [A-Z ]+-----[\s\S]*?-----END [A-Z ]+-----', '[REDACTED-PEM-KEY]'),
        # Credit Card Numbers (basic)
        (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', '[REDACTED-CC]'),
        # Email addresses (partial redaction)
        (r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'[REDACTED]@\2'),
        # Phone numbers
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED-PHONE]'),
    ]
    
    redacted = text
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
    
    return redacted

# High-entropy string detection fallback
def _has_high_entropy(text: str, threshold: float = 4.0) -> bool:
    """Simple entropy calculation for fallback detection"""
    if len(text) < 8:
        return False
    
    import math
    from collections import Counter
    
    # Calculate Shannon entropy
    counts = Counter(text)
    length = len(text)
    entropy = -sum((count / length) * math.log2(count / length) for count in counts.values())
    
    return entropy > threshold

def enhanced_detector_fn(text: str) -> str:
    """Enhanced detector with entropy-based detection"""
    # First apply pattern-based redaction
    redacted = detector_fn(text)
    
    # Then check for high-entropy strings that might be secrets
    words = redacted.split()
    for i, word in enumerate(words):
        if len(word) > 16 and _has_high_entropy(word):
            words[i] = '[REDACTED-HIGH-ENTROPY]'
    
    return ' '.join(words)