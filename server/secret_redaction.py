#!/usr/bin/env python3
"""
Secret Redaction Pipeline - Prevents credential leaks in logs and memory
Critical P0 security fix identified in external code review
"""

import re
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class SecretDetector:
    """Detects various types of secrets and credentials"""
    
    def __init__(self):
        self.patterns = {
            'jwt_token': [
                r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',  # JWT tokens
                r'Bearer\s+[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'
            ],
            'api_key': [
                r'(?i)api[_-]?key["\s]*[:=]["\s]*[A-Za-z0-9_-]{20,}',
                r'(?i)secret[_-]?key["\s]*[:=]["\s]*[A-Za-z0-9_-]{20,}',
                r'(?i)access[_-]?token["\s]*[:=]["\s]*[A-Za-z0-9_-]{20,}',
                r'sk-[A-Za-z0-9]{32,}',  # OpenAI-style API keys
                r'[A-Za-z0-9_-]{32,64}'  # Generic long tokens
            ],
            'password': [
                r'(?i)password["\s]*[:=]["\s]*["\'][^"\']{8,}["\']',
                r'(?i)passwd["\s]*[:=]["\s]*["\'][^"\']{8,}["\']'
            ],
            'database_url': [
                r'postgresql://[^:]+:[^@]+@[^/]+/\w+',
                r'mysql://[^:]+:[^@]+@[^/]+/\w+',
                r'mongodb://[^:]+:[^@]+@[^/]+/\w+'
            ],
            'private_key': [
                r'-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+PRIVATE KEY-----',
                r'-----BEGIN RSA PRIVATE KEY-----[\s\S]*?-----END RSA PRIVATE KEY-----'
            ],
            'aws_credentials': [
                r'AKIA[0-9A-Z]{16}',  # AWS Access Key ID
                r'(?i)aws[_-]?secret[_-]?access[_-]?key["\s]*[:=]["\s]*[A-Za-z0-9/+=]{40}'
            ]
        }
    
    def detect_secrets(self, text: str) -> List[Dict[str, Any]]:
        """Detect secrets in text and return findings"""
        findings = []
        
        for secret_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    findings.append({
                        'type': secret_type,
                        'start': match.start(),
                        'end': match.end(),
                        'matched_text': match.group(),
                        'pattern': pattern
                    })
        
        return findings
    
    def redact_secrets(self, text: str, replacement: str = "[REDACTED]") -> str:
        """Redact detected secrets from text"""
        findings = self.detect_secrets(text)
        
        # Sort by position (reverse order to maintain indices)
        findings.sort(key=lambda x: x['start'], reverse=True)
        
        redacted_text = text
        for finding in findings:
            redacted_text = (
                redacted_text[:finding['start']] + 
                f"[REDACTED_{finding['type'].upper()}]" + 
                redacted_text[finding['end']:]
            )
        
        return redacted_text

class SecretRedactionPipeline:
    """Main pipeline for secret redaction across the system"""
    
    def __init__(self):
        self.detector = SecretDetector()
        self.redaction_log = []
        self.enabled = True
    
    def redact_memory_data(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact secrets from memory data before storage"""
        if not self.enabled:
            return memory_data
        
        redacted_data = memory_data.copy()
        
        # Redact text content
        if 'text' in redacted_data:
            original_text = redacted_data['text']
            redacted_text = self.detector.redact_secrets(original_text)
            
            if original_text != redacted_text:
                self._log_redaction('memory_storage', original_text, redacted_text)
                redacted_data['text'] = redacted_text
        
        # Redact JSON data recursively
        if 'data' in redacted_data and isinstance(redacted_data['data'], dict):
            redacted_data['data'] = self._redact_dict_recursive(redacted_data['data'])
        
        return redacted_data
    
    def redact_log_message(self, message: str) -> str:
        """Redact secrets from log messages"""
        if not self.enabled:
            return message
        
        redacted_message = self.detector.redact_secrets(message)
        
        if message != redacted_message:
            self._log_redaction('log_message', message, redacted_message)
        
        return redacted_message
    
    def redact_api_response(self, response_data: Any) -> Any:
        """Redact secrets from API responses"""
        if not self.enabled:
            return response_data
        
        if isinstance(response_data, dict):
            return self._redact_dict_recursive(response_data)
        elif isinstance(response_data, str):
            return self.detector.redact_secrets(response_data)
        else:
            return response_data
    
    def _redact_dict_recursive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact secrets from dictionary"""
        redacted = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                redacted[key] = self.detector.redact_secrets(value)
            elif isinstance(value, dict):
                redacted[key] = self._redact_dict_recursive(value)
            elif isinstance(value, list):
                redacted[key] = [
                    self.detector.redact_secrets(item) if isinstance(item, str)
                    else self._redact_dict_recursive(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                redacted[key] = value
        
        return redacted
    
    def _log_redaction(self, source: str, original: str, redacted: str):
        """Log redaction events for security monitoring"""
        redaction_event = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': source,
            'original_length': len(original),
            'redacted_length': len(redacted),
            'secrets_found': len(self.detector.detect_secrets(original))
        }
        
        self.redaction_log.append(redaction_event)
        
        # Keep only last 1000 events
        if len(self.redaction_log) > 1000:
            self.redaction_log = self.redaction_log[-1000:]
    
    def get_redaction_stats(self) -> Dict[str, Any]:
        """Get statistics about redaction activity"""
        if not self.redaction_log:
            return {'total_redactions': 0, 'sources': {}}
        
        stats = {
            'total_redactions': len(self.redaction_log),
            'sources': {},
            'last_24h': 0
        }
        
        # Count by source
        for event in self.redaction_log:
            source = event['source']
            stats['sources'][source] = stats['sources'].get(source, 0) + 1
        
        # Count last 24 hours
        now = datetime.utcnow()
        for event in self.redaction_log:
            event_time = datetime.fromisoformat(event['timestamp'])
            if (now - event_time).total_seconds() < 86400:  # 24 hours
                stats['last_24h'] += 1
        
        return stats

# Global instance
_redaction_pipeline = None

def get_redaction_pipeline() -> SecretRedactionPipeline:
    """Get global redaction pipeline instance"""
    global _redaction_pipeline
    if _redaction_pipeline is None:
        _redaction_pipeline = SecretRedactionPipeline()
    return _redaction_pipeline

def redact_memory_before_storage(memory_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for memory redaction"""
    pipeline = get_redaction_pipeline()
    return pipeline.redact_memory_data(memory_data)

def redact_log_message(message: str) -> str:
    """Convenience function for log redaction"""
    pipeline = get_redaction_pipeline()
    return pipeline.redact_log_message(message)

def redact_api_response(response_data: Any) -> Any:
    """Convenience function for API response redaction"""
    pipeline = get_redaction_pipeline()
    return pipeline.redact_api_response(response_data)

# Test function
def test_secret_detection():
    """Test the secret detection and redaction"""
    test_cases = [
        "JWT token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjN9.signature",
        "API key: sk-1234567890abcdef1234567890abcdef",
        "Database: postgresql://user:password123@localhost:5432/db",
        "Password: 'mySecretPassword123'",
        "AWS key: AKIAIOSFODNN7EXAMPLE"
    ]
    
    detector = SecretDetector()
    
    for test_case in test_cases:
        print(f"Original: {test_case}")
        redacted = detector.redact_secrets(test_case)
        print(f"Redacted: {redacted}")
        print("---")

if __name__ == "__main__":
    test_secret_detection()
