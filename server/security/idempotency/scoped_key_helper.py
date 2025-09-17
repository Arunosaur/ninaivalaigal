"""
Scoped Idempotency Key Helper

Utility functions for generating and validating scoped idempotency keys
with path template extraction and collision avoidance.
"""

import re
import hashlib
from typing import Optional, Dict, Any, Tuple
from urllib.parse import unquote


class ScopedKeyHelper:
    """Helper for scoped idempotency key generation and validation."""
    
    # Path template patterns for common route structures
    PATH_PATTERNS = [
        # Organization IDs (org_ prefix) - must come before generic alphanumeric
        (r'/org_[a-zA-Z0-9-]+', '/{org_id}'),
        # Team IDs (team_ prefix) - must come before generic alphanumeric
        (r'/team_[a-zA-Z0-9-]+', '/{team_id}'),
        # Memory IDs (mem_ prefix) - must come before generic alphanumeric
        (r'/mem_[a-zA-Z0-9-]+', '/{memory_id}'),
        # Context IDs (ctx_ prefix) - must come before generic alphanumeric
        (r'/ctx_[a-zA-Z0-9-]+', '/{context_id}'),
        # UUID patterns - must come before numeric IDs
        (r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}'),
        # Numeric IDs (pure numbers)
        (r'/\d+', '/{id}'),
        # Alphanumeric with hyphens that look like IDs
        (r'/[a-zA-Z0-9]+-[a-zA-Z0-9-]+', '/{id}'),
        # Mixed alphanumeric that contains numbers (likely IDs)
        (r'/[a-zA-Z]*\d+[a-zA-Z0-9]*', '/{id}'),
    ]
    
    @classmethod
    def extract_path_template(cls, path: str) -> str:
        """
        Extract path template from actual request path.
        
        Converts /memories/123/contexts/456 -> /memories/{id}/contexts/{id}
        """
        if not path:
            return "/"
        
        # URL decode first
        decoded_path = unquote(path)
        
        # Remove query parameters
        if '?' in decoded_path:
            decoded_path = decoded_path.split('?')[0]
        
        # Apply path patterns
        template = decoded_path
        for pattern, replacement in cls.PATH_PATTERNS:
            template = re.sub(pattern, replacement, template)
        
        return template
    
    @classmethod
    def generate_scoped_key(
        cls,
        method: str,
        path: str,
        subject_user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> str:
        """
        Generate scoped idempotency key.
        
        Format: {method}:{path_template}:{user_id}:{org_id}:{path_hash}:{key_hash}
        """
        # Extract path template
        path_template = cls.extract_path_template(path)
        
        # Create hash of concrete path to prevent collisions on same template
        path_hash = hashlib.sha256(path.encode()).hexdigest()[:8]
        
        # Build scope components
        components = [
            method.upper(),
            path_template,
            subject_user_id or "anonymous",
            organization_id or "default",
            path_hash,
        ]
        
        # Add idempotency key hash if provided
        if idempotency_key:
            key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()[:16]
            components.append(key_hash)
        else:
            components.append("no-key")
        
        return ":".join(components)
    
    @classmethod
    def parse_scoped_key(cls, scoped_key: str) -> Dict[str, str]:
        """Parse scoped key back into components."""
        parts = scoped_key.split(":")
        
        if len(parts) < 6:
            raise ValueError(f"Invalid scoped key format: {scoped_key}")
        
        return {
            "method": parts[0],
            "path_template": parts[1], 
            "subject_user_id": parts[2] if parts[2] != "anonymous" else None,
            "organization_id": parts[3] if parts[3] != "default" else None,
            "path_hash": parts[4],
            "key_hash": parts[5] if parts[5] != "no-key" else None
        }
    
    @classmethod
    def validate_key_scope(cls, scoped_key: str, method: str, path: str, user_id: Optional[str] = None) -> bool:
        """Validate that scoped key matches current request context."""
        try:
            parsed = cls.parse_scoped_key(scoped_key)
            
            # Check method match
            if parsed["method"] != method.upper():
                return False
            
            # Check path template match
            expected_template = cls.extract_path_template(path)
            if parsed["path_template"] != expected_template:
                return False
            
            # Check path hash match
            expected_path_hash = hashlib.sha256(path.encode()).hexdigest()[:8]
            if parsed["path_hash"] != expected_path_hash:
                return False
            
            # Check user context match
            expected_user = user_id or "anonymous"
            actual_user = parsed["subject_user_id"] or "anonymous"
            if actual_user != expected_user:
                return False
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    @classmethod
    def get_collision_info(cls, key1: str, key2: str) -> Dict[str, Any]:
        """Analyze potential collision between two scoped keys."""
        try:
            parsed1 = cls.parse_scoped_key(key1)
            parsed2 = cls.parse_scoped_key(key2)
            
            collisions = []
            
            # Check each component for collision
            if parsed1["method"] == parsed2["method"]:
                collisions.append("method")
            
            if parsed1["path_template"] == parsed2["path_template"]:
                collisions.append("path_template")
            
            if parsed1["subject_user_id"] == parsed2["subject_user_id"]:
                collisions.append("subject_user_id")
            
            if parsed1["organization_id"] == parsed2["organization_id"]:
                collisions.append("organization_id")
            
            if parsed1["path_hash"] == parsed2["path_hash"]:
                collisions.append("path_hash")
            
            if parsed1["key_hash"] == parsed2["key_hash"]:
                collisions.append("key_hash")
            
            # Full collision if all components match
            full_collision = len(collisions) == 6
            
            return {
                "full_collision": full_collision,
                "partial_collisions": collisions,
                "collision_risk": len(collisions) / 6.0,
                "key1_parsed": parsed1,
                "key2_parsed": parsed2
            }
            
        except ValueError as e:
            return {
                "full_collision": False,
                "error": str(e),
                "collision_risk": 0.0
            }


def scope_get(method: str, path: str, user_id: Optional[str] = None) -> str:
    """Quick helper for GET request scoped keys."""
    return ScopedKeyHelper.generate_scoped_key(method, path, user_id)


def scope_post(method: str, path: str, user_id: Optional[str] = None, idempotency_key: Optional[str] = None) -> str:
    """Quick helper for POST request scoped keys with idempotency."""
    return ScopedKeyHelper.generate_scoped_key(method, path, user_id, idempotency_key=idempotency_key)


def test_scoped_key_helper():
    """Test scoped idempotency key helper functionality."""
    
    test_cases = [
        # Path template extraction
        {
            "path": "/memories/123/contexts/456",
            "expected_template": "/memories/{id}/contexts/{id}"
        },
        {
            "path": "/organizations/org_abc123/teams/team_xyz789",
            "expected_template": "/organizations/{org_id}/teams/{team_id}"
        },
        {
            "path": "/users/550e8400-e29b-41d4-a716-446655440000/profile",
            "expected_template": "/users/{uuid}/profile"
        },
        # Scoped key generation
        {
            "method": "POST",
            "path": "/memories/123",
            "user_id": "user_456",
            "org_id": "org_789",
            "key": "abc123",
            "expected_format": "POST:/memories/{id}:user_456:org_789:"
        }
    ]
    
    results = []
    
    # Test path template extraction
    for case in test_cases[:3]:
        template = ScopedKeyHelper.extract_path_template(case["path"])
        test_passed = template == case["expected_template"]
        
        results.append({
            "test": "path_template",
            "input": case["path"],
            "expected": case["expected_template"],
            "actual": template,
            "passed": test_passed
        })
    
    # Test scoped key generation
    case = test_cases[3]
    scoped_key = ScopedKeyHelper.generate_scoped_key(
        case["method"],
        case["path"], 
        case["user_id"],
        case["org_id"],
        case["key"]
    )
    
    # Check format (first 4 components)
    key_parts = scoped_key.split(":")
    actual_prefix = ":".join(key_parts[:4]) + ":"
    test_passed = actual_prefix == case["expected_format"]
    
    results.append({
        "test": "scoped_key_generation",
        "scoped_key": scoped_key,
        "expected_prefix": case["expected_format"],
        "actual_prefix": actual_prefix,
        "passed": test_passed
    })
    
    # Test key parsing and validation
    parsed = ScopedKeyHelper.parse_scoped_key(scoped_key)
    validation_passed = ScopedKeyHelper.validate_key_scope(
        scoped_key, 
        case["method"],
        case["path"],
        case["user_id"]
    )
    
    results.append({
        "test": "key_parsing_validation",
        "parsed": parsed,
        "validation_passed": validation_passed,
        "passed": validation_passed
    })
    
    # Test collision detection
    key1 = ScopedKeyHelper.generate_scoped_key("POST", "/memories/123", "user1", "org1", "key1")
    key2 = ScopedKeyHelper.generate_scoped_key("POST", "/memories/456", "user1", "org1", "key2")
    
    collision_info = ScopedKeyHelper.get_collision_info(key1, key2)
    
    results.append({
        "test": "collision_detection",
        "key1": key1,
        "key2": key2,
        "collision_info": collision_info,
        "passed": not collision_info["full_collision"] and collision_info["collision_risk"] < 1.0
    })
    
    return {
        "total_tests": len(results),
        "passed_tests": sum(1 for r in results if r["passed"]),
        "test_results": results
    }


if __name__ == "__main__":
    # Run tests
    test_results = test_scoped_key_helper()
    print("Scoped Idempotency Key Helper Test Results:")
    print(f"Passed: {test_results['passed_tests']}/{test_results['total_tests']}")
    
    for result in test_results["test_results"]:
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {result['test']}: {result.get('actual', 'N/A')}")
