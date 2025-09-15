#!/usr/bin/env python3
"""
Input Validation and Sanitization - Critical P0 security fix
Comprehensive input validation for all API endpoints and user inputs
"""

import re
import html
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, validator, EmailStr
from email_validator import validate_email, EmailNotValidError

class InputValidationError(Exception):
    """Custom exception for input validation errors"""
    pass

class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    def __init__(self):
        # Maximum lengths for various input types
        self.max_lengths = {
            'name': 100,
            'email': 254,  # RFC 5321 limit
            'password': 128,
            'description': 1000,
            'context_name': 100,
            'memory_text': 10000,
            'organization_name': 100,
            'team_name': 100,
            'message': 2000,
            'url': 2048,
            'filename': 255
        }
        
        # Regex patterns for validation
        self.patterns = {
            'name': r'^[a-zA-Z0-9\s\-_.]{1,100}$',
            'username': r'^[a-zA-Z0-9_-]{3,50}$',
            'context_name': r'^[a-zA-Z0-9\s\-_.]{1,100}$',
            'team_name': r'^[a-zA-Z0-9\s\-_.]{1,100}$',
            'organization_name': r'^[a-zA-Z0-9\s\-_.]{1,100}$',
            'alphanumeric': r'^[a-zA-Z0-9]+$',
            'safe_filename': r'^[a-zA-Z0-9\-_.]{1,255}$'
        }
        
        # Dangerous patterns to block
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',               # JavaScript URLs
            r'on\w+\s*=',                # Event handlers
            r'<iframe[^>]*>',            # Iframes
            r'<object[^>]*>',            # Objects
            r'<embed[^>]*>',             # Embeds
            r'eval\s*\(',                # eval() calls
            r'document\.',               # DOM access
            r'window\.',                 # Window object access
            r'\.innerHTML',              # innerHTML manipulation
            r'UNION\s+SELECT',           # SQL injection
            r'DROP\s+TABLE',             # SQL injection
            r'DELETE\s+FROM',            # SQL injection
            r'INSERT\s+INTO',            # SQL injection
            r'UPDATE\s+SET',             # SQL injection
        ]
    
    def validate_string(self, value: str, field_name: str, max_length: Optional[int] = None, 
                       pattern: Optional[str] = None, allow_empty: bool = False) -> str:
        """Validate and sanitize string input"""
        if not isinstance(value, str):
            raise InputValidationError(f"{field_name} must be a string")
        
        # Check for empty values
        if not value.strip() and not allow_empty:
            raise InputValidationError(f"{field_name} cannot be empty")
        
        # Check length
        max_len = max_length or self.max_lengths.get(field_name, 1000)
        if len(value) > max_len:
            raise InputValidationError(f"{field_name} exceeds maximum length of {max_len}")
        
        # Check for dangerous patterns
        for dangerous_pattern in self.dangerous_patterns:
            if re.search(dangerous_pattern, value, re.IGNORECASE):
                raise InputValidationError(f"{field_name} contains potentially dangerous content")
        
        # Apply pattern validation
        if pattern:
            if not re.match(pattern, value):
                raise InputValidationError(f"{field_name} format is invalid")
        elif field_name in self.patterns:
            if not re.match(self.patterns[field_name], value):
                raise InputValidationError(f"{field_name} format is invalid")
        
        # HTML escape for safety
        return html.escape(value.strip())
    
    def validate_email(self, email: str) -> str:
        """Validate email address"""
        if not isinstance(email, str):
            raise InputValidationError("Email must be a string")
        
        # Basic email validation using regex (fallback if email-validator not available)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise InputValidationError("Invalid email address format")
        
        return email.lower().strip()
    
    def validate_password(self, password: str) -> str:
        """Validate password strength"""
        if not isinstance(password, str):
            raise InputValidationError("Password must be a string")
        
        if len(password) < 8:
            raise InputValidationError("Password must be at least 8 characters long")
        
        if len(password) > self.max_lengths['password']:
            raise InputValidationError(f"Password exceeds maximum length of {self.max_lengths['password']}")
        
        # Check for at least one letter and one number
        if not re.search(r'[A-Za-z]', password):
            raise InputValidationError("Password must contain at least one letter")
        
        if not re.search(r'\d', password):
            raise InputValidationError("Password must contain at least one number")
        
        # Check for dangerous patterns
        for dangerous_pattern in self.dangerous_patterns:
            if re.search(dangerous_pattern, password, re.IGNORECASE):
                raise InputValidationError("Password contains invalid characters")
        
        return password  # Don't escape passwords
    
    def validate_integer(self, value: Any, field_name: str, min_value: Optional[int] = None, 
                        max_value: Optional[int] = None) -> int:
        """Validate integer input"""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise InputValidationError(f"{field_name} must be a valid integer")
        
        if min_value is not None and int_value < min_value:
            raise InputValidationError(f"{field_name} must be at least {min_value}")
        
        if max_value is not None and int_value > max_value:
            raise InputValidationError(f"{field_name} must be at most {max_value}")
        
        return int_value
    
    def validate_json(self, value: str, field_name: str) -> Dict[str, Any]:
        """Validate and parse JSON input"""
        if not isinstance(value, str):
            raise InputValidationError(f"{field_name} must be a JSON string")
        
        try:
            parsed_json = json.loads(value)
        except json.JSONDecodeError as e:
            raise InputValidationError(f"{field_name} is not valid JSON: {str(e)}")
        
        # Validate JSON structure recursively
        self._validate_json_recursive(parsed_json, field_name)
        
        return parsed_json
    
    def validate_list(self, value: Any, field_name: str, max_items: int = 100, 
                     item_validator: Optional[callable] = None) -> List[Any]:
        """Validate list input"""
        if not isinstance(value, list):
            raise InputValidationError(f"{field_name} must be a list")
        
        if len(value) > max_items:
            raise InputValidationError(f"{field_name} cannot have more than {max_items} items")
        
        if item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_item = item_validator(item)
                    validated_items.append(validated_item)
                except Exception as e:
                    raise InputValidationError(f"{field_name}[{i}]: {str(e)}")
            return validated_items
        
        return value
    
    def sanitize_html(self, value: str) -> str:
        """Sanitize HTML content"""
        if not isinstance(value, str):
            return str(value)
        
        # Remove dangerous HTML tags and attributes
        sanitized = html.escape(value)
        
        # Additional sanitization for specific patterns
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _validate_json_recursive(self, obj: Any, field_name: str, depth: int = 0):
        """Recursively validate JSON object structure"""
        if depth > 10:  # Prevent deep nesting attacks
            raise InputValidationError(f"{field_name} has excessive nesting depth")
        
        if isinstance(obj, dict):
            if len(obj) > 100:  # Prevent large object attacks
                raise InputValidationError(f"{field_name} has too many keys")
            
            for key, value in obj.items():
                if not isinstance(key, str):
                    raise InputValidationError(f"{field_name} contains non-string key")
                
                if len(key) > 100:
                    raise InputValidationError(f"{field_name} contains overly long key")
                
                self._validate_json_recursive(value, f"{field_name}.{key}", depth + 1)
        
        elif isinstance(obj, list):
            if len(obj) > 1000:  # Prevent large array attacks
                raise InputValidationError(f"{field_name} contains too many items")
            
            for i, item in enumerate(obj):
                self._validate_json_recursive(item, f"{field_name}[{i}]", depth + 1)
        
        elif isinstance(obj, str):
            if len(obj) > 10000:  # Prevent large string attacks
                raise InputValidationError(f"{field_name} contains overly long string")
            
            # Check for dangerous patterns in string values
            for dangerous_pattern in self.dangerous_patterns:
                if re.search(dangerous_pattern, obj, re.IGNORECASE):
                    raise InputValidationError(f"{field_name} contains potentially dangerous content")

class APIInputValidator:
    """Specialized validator for API inputs"""
    
    def __init__(self):
        self.validator = InputValidator()
    
    def validate_signup_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user signup data"""
        validated = {}
        
        validated['email'] = self.validator.validate_email(data.get('email', ''))
        validated['password'] = self.validator.validate_password(data.get('password', ''))
        validated['name'] = self.validator.validate_string(data.get('name', ''), 'name')
        
        if 'account_type' in data:
            account_type = data['account_type']
            if account_type not in ['individual', 'organization']:
                raise InputValidationError("Invalid account type")
            validated['account_type'] = account_type
        
        return validated
    
    def validate_login_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user login data"""
        validated = {}
        
        validated['email'] = self.validator.validate_email(data.get('email', ''))
        validated['password'] = self.validator.validate_string(
            data.get('password', ''), 'password', max_length=128, allow_empty=False
        )
        
        return validated
    
    def validate_memory_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate memory storage data"""
        validated = {}
        
        validated['text'] = self.validator.validate_string(
            data.get('text', ''), 'memory_text', max_length=10000
        )
        
        if 'context' in data:
            validated['context'] = self.validator.validate_string(
                data['context'], 'context_name', allow_empty=True
            )
        
        return validated
    
    def validate_context_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate context creation data"""
        validated = {}
        
        validated['name'] = self.validator.validate_string(data.get('name', ''), 'context_name')
        
        if 'description' in data:
            validated['description'] = self.validator.validate_string(
                data['description'], 'description', allow_empty=True
            )
        
        if 'scope' in data:
            scope = data['scope']
            if scope not in ['personal', 'team', 'organization']:
                raise InputValidationError("Invalid context scope")
            validated['scope'] = scope
        
        return validated

# Global instance
_input_validator = None
_api_validator = None

def get_input_validator() -> InputValidator:
    """Get global input validator instance"""
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
    return _input_validator

def get_api_validator() -> APIInputValidator:
    """Get global API input validator instance"""
    global _api_validator
    if _api_validator is None:
        _api_validator = APIInputValidator()
    return _api_validator

# Convenience functions
def validate_string(value: str, field_name: str, **kwargs) -> str:
    """Convenience function for string validation"""
    validator = get_input_validator()
    return validator.validate_string(value, field_name, **kwargs)

def validate_email(email: str) -> str:
    """Convenience function for email validation"""
    validator = get_input_validator()
    return validator.validate_email(email)

def validate_password(password: str) -> str:
    """Convenience function for password validation"""
    validator = get_input_validator()
    return validator.validate_password(password)

# Test function
def test_input_validation():
    """Test the input validation system"""
    validator = InputValidator()
    
    # Test dangerous input detection
    dangerous_inputs = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "'; DROP TABLE users; --",
        "UNION SELECT * FROM passwords",
        "<iframe src='evil.com'></iframe>"
    ]
    
    print("Testing dangerous input detection:")
    for dangerous_input in dangerous_inputs:
        try:
            validator.validate_string(dangerous_input, "test_field")
            print(f"FAILED: Should have blocked: {dangerous_input}")
        except InputValidationError:
            print(f"PASSED: Blocked dangerous input: {dangerous_input[:50]}...")
    
    # Test valid inputs
    valid_inputs = [
        ("test@example.com", "email"),
        ("ValidName123", "name"),
        ("SecurePass123", "password")
    ]
    
    print("\nTesting valid inputs:")
    for value, field_type in valid_inputs:
        try:
            if field_type == "email":
                result = validator.validate_email(value)
            elif field_type == "password":
                result = validator.validate_password(value)
            else:
                result = validator.validate_string(value, field_type)
            print(f"PASSED: Valid {field_type}: {value}")
        except Exception as e:
            print(f"FAILED: Valid {field_type} rejected: {value} - {e}")

if __name__ == "__main__":
    test_input_validation()
