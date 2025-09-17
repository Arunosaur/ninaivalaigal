"""
Binary Masquerade Heuristic for Multipart

Detects binary files masquerading as text to prevent security bypasses
through content-type spoofing and file extension manipulation.
"""

import re
from typing import Dict, Any, Optional, Tuple, List


class BinaryMasqueradeDetector:
    """Detects binary content masquerading as text."""
    
    # Binary file signatures (magic bytes)
    BINARY_SIGNATURES = {
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'\xff\xd8\xff': 'image/jpeg',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'%PDF-': 'application/pdf',
        b'PK\x03\x04': 'application/zip',
        b'PK\x05\x06': 'application/zip',
        b'PK\x07\x08': 'application/zip',
        b'\x00\x00\x01\x00': 'image/x-icon',
        b'RIFF': 'audio/wav',
        b'\x1f\x8b\x08': 'application/gzip',
        b'BM': 'image/bmp',
        b'\x00\x00\x00\x18ftypmp4': 'video/mp4',
        b'\x00\x00\x00 ftypM4A': 'audio/mp4',
        b'ID3': 'audio/mpeg',
        b'\xff\xfb': 'audio/mpeg',
        b'\x4d\x5a': 'application/x-msdownload',  # PE executable
        b'\x7f\x45\x4c\x46': 'application/x-executable',  # ELF executable
    }
    
    # High-entropy byte patterns that suggest binary content
    BINARY_BYTE_PATTERNS = [
        b'\x00',  # Null bytes
        b'\xff\xfe',  # UTF-16 BOM
        b'\xfe\xff',  # UTF-16 BE BOM
        b'\xef\xbb\xbf',  # UTF-8 BOM
    ]
    
    def __init__(self, max_check_bytes: int = 1024):
        self.max_check_bytes = max_check_bytes
    
    def detect_masquerade(self, content: bytes, declared_content_type: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect if binary content is masquerading as text.
        
        Returns detection result with confidence score and details.
        """
        result = {
            "is_masquerade": False,
            "confidence": 0.0,
            "detected_type": None,
            "declared_type": declared_content_type,
            "filename": filename,
            "evidence": []
        }
        
        if not content:
            return result
        
        # Check first bytes for binary signatures
        signature_result = self._check_binary_signatures(content[:self.max_check_bytes])
        if signature_result["detected"]:
            result["evidence"].append("binary_signature")
            result["detected_type"] = signature_result["type"]
            result["confidence"] += 0.8
        
        # Check for null bytes (strong binary indicator)
        null_byte_result = self._check_null_bytes(content[:self.max_check_bytes])
        if null_byte_result["detected"]:
            result["evidence"].append("null_bytes")
            result["confidence"] += 0.7
        
        # Check entropy (high entropy suggests binary)
        entropy_result = self._check_entropy(content[:self.max_check_bytes])
        if entropy_result["high_entropy"]:
            result["evidence"].append("high_entropy")
            result["confidence"] += 0.3
        
        # Check non-printable character ratio
        printable_result = self._check_printable_ratio(content[:self.max_check_bytes])
        if printable_result["low_printable"]:
            result["evidence"].append("low_printable_ratio")
            result["confidence"] += 0.4
        
        # Check content-type vs detected type mismatch
        if result["detected_type"] and not self._types_compatible(declared_content_type, result["detected_type"]):
            result["evidence"].append("content_type_mismatch")
            result["confidence"] += 0.5
        
        # Check filename extension mismatch
        if filename:
            extension_result = self._check_extension_mismatch(filename, declared_content_type, result["detected_type"])
            if extension_result["mismatch"]:
                result["evidence"].append("extension_mismatch")
                result["confidence"] += 0.3
        
        # Determine if masquerade detected
        result["is_masquerade"] = result["confidence"] >= 0.6
        result["confidence"] = min(result["confidence"], 1.0)
        
        return result
    
    def _check_binary_signatures(self, content: bytes) -> Dict[str, Any]:
        """Check for known binary file signatures."""
        for signature, file_type in self.BINARY_SIGNATURES.items():
            if content.startswith(signature):
                return {"detected": True, "type": file_type, "signature": signature.hex()}
        
        return {"detected": False, "type": None, "signature": None}
    
    def _check_null_bytes(self, content: bytes) -> Dict[str, Any]:
        """Check for null bytes which indicate binary content."""
        null_count = content.count(b'\x00')
        total_bytes = len(content)
        
        if total_bytes == 0:
            return {"detected": False, "ratio": 0.0}
        
        null_ratio = null_count / total_bytes
        
        # Even a small percentage of null bytes suggests binary
        return {
            "detected": null_ratio > 0.01,  # 1% threshold
            "ratio": null_ratio,
            "count": null_count
        }
    
    def _check_entropy(self, content: bytes) -> Dict[str, Any]:
        """Check entropy to detect compressed/encrypted binary content."""
        if not content:
            return {"high_entropy": False, "entropy": 0.0}
        
        # Calculate Shannon entropy
        byte_counts = [0] * 256
        for byte in content:
            byte_counts[byte] += 1
        
        entropy = 0.0
        content_length = len(content)
        
        for count in byte_counts:
            if count > 0:
                probability = count / content_length
                import math
                entropy -= probability * math.log2(probability)
        
        # High entropy (> 7.5) suggests compressed/encrypted binary
        return {
            "high_entropy": entropy > 7.5,
            "entropy": entropy
        }
    
    def _check_printable_ratio(self, content: bytes) -> Dict[str, Any]:
        """Check ratio of printable ASCII characters."""
        if not content:
            return {"low_printable": False, "ratio": 0.0}
        
        printable_count = 0
        for byte in content:
            # Printable ASCII range (32-126) plus common whitespace
            if 32 <= byte <= 126 or byte in [9, 10, 13]:  # tab, newline, carriage return
                printable_count += 1
        
        printable_ratio = printable_count / len(content)
        
        # Low printable ratio suggests binary
        return {
            "low_printable": printable_ratio < 0.7,  # 70% threshold
            "ratio": printable_ratio
        }
    
    def _types_compatible(self, declared_type: str, detected_type: str) -> bool:
        """Check if declared and detected content types are compatible."""
        if not declared_type or not detected_type:
            return True
        
        # Normalize types
        declared_main = declared_type.split('/')[0].lower()
        detected_main = detected_type.split('/')[0].lower()
        
        # Text types should not be detected as binary types
        if declared_main == 'text' and detected_main in ['image', 'audio', 'video', 'application']:
            return False
        
        # Application/json should not be detected as binary
        if declared_type.lower() == 'application/json' and detected_main in ['image', 'audio', 'video']:
            return False
        
        return True
    
    def _check_extension_mismatch(self, filename: str, declared_type: str, detected_type: Optional[str]) -> Dict[str, Any]:
        """Check for filename extension vs content type mismatch."""
        if not filename or '.' not in filename:
            return {"mismatch": False}
        
        extension = filename.split('.')[-1].lower()
        
        # Common extension to content-type mappings
        extension_types = {
            'txt': 'text/plain',
            'json': 'application/json',
            'html': 'text/html',
            'css': 'text/css',
            'js': 'application/javascript',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'pdf': 'application/pdf',
            'zip': 'application/zip',
            'exe': 'application/x-msdownload',
            'dll': 'application/x-msdownload',
        }
        
        expected_type = extension_types.get(extension)
        
        # Check mismatch with detected type (higher priority)
        if detected_type and expected_type:
            mismatch = not self._types_compatible(expected_type, detected_type)
            return {
                "mismatch": mismatch,
                "extension": extension,
                "expected_type": expected_type,
                "detected_type": detected_type
            }
        
        # Fallback to declared type check
        if expected_type and declared_type:
            mismatch = not self._types_compatible(expected_type, declared_type)
            return {
                "mismatch": mismatch,
                "extension": extension,
                "expected_type": expected_type,
                "declared_type": declared_type
            }
        
        return {"mismatch": False}


def looks_binary(content: bytes, declared_content_type: str, filename: Optional[str] = None, threshold: float = 0.6) -> bool:
    """
    Simple heuristic to check if content looks binary despite declared type.
    
    Args:
        content: File content bytes
        declared_content_type: Declared MIME type
        filename: Optional filename
        threshold: Confidence threshold for binary detection
    
    Returns:
        True if content appears to be binary masquerading as text
    """
    detector = BinaryMasqueradeDetector()
    result = detector.detect_masquerade(content, declared_content_type, filename)
    return result["is_masquerade"] and result["confidence"] >= threshold


def test_binary_masquerade_detection():
    """Test binary masquerade detection."""
    detector = BinaryMasqueradeDetector()
    
    test_cases = [
        # PNG file with text content-type (should detect)
        {
            "content": b'\x89PNG\r\n\x1a\n' + b'fake_png_data' * 50,
            "declared_type": "text/plain",
            "filename": "image.txt",
            "should_detect": True
        },
        # Actual text content (should not detect)
        {
            "content": b"This is normal text content with some numbers 12345",
            "declared_type": "text/plain", 
            "filename": "document.txt",
            "should_detect": False
        },
        # Binary with null bytes (should detect)
        {
            "content": b"text\x00\x00binary\x00content" * 20,
            "declared_type": "application/json",
            "filename": "data.json",
            "should_detect": True
        },
        # PDF masquerading as text (should detect)
        {
            "content": b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog' + b'\x00' * 100,
            "declared_type": "text/plain",
            "filename": "document.txt", 
            "should_detect": True
        }
    ]
    
    results = []
    for i, case in enumerate(test_cases):
        result = detector.detect_masquerade(
            case["content"],
            case["declared_type"],
            case["filename"]
        )
        
        test_passed = result["is_masquerade"] == case["should_detect"]
        
        results.append({
            "test_case": i + 1,
            "expected_detection": case["should_detect"],
            "actual_detection": result["is_masquerade"],
            "confidence": result["confidence"],
            "evidence": result["evidence"],
            "test_passed": test_passed
        })
    
    return {
        "total_tests": len(test_cases),
        "passed_tests": sum(1 for r in results if r["test_passed"]),
        "test_results": results
    }


if __name__ == "__main__":
    # Run tests
    test_results = test_binary_masquerade_detection()
    print("Binary Masquerade Detection Test Results:")
    print(f"Passed: {test_results['passed_tests']}/{test_results['total_tests']}")
    
    for result in test_results["test_results"]:
        status = "✅" if result["test_passed"] else "❌"
        print(f"{status} Test {result['test_case']}: {result['confidence']:.2f} confidence, evidence: {result['evidence']}")
