"""
Masquerade Byte Cap

Bounds CPU usage for binary masquerade detection by capping bytes inspected
to min(content_length, 256*1024) for magic/entropy analysis.
"""

from typing import Any

from .binary_masquerade_guard import BinaryMasqueradeDetector


class BoundedBinaryMasqueradeDetector(BinaryMasqueradeDetector):
    """Binary masquerade detector with CPU-bounded analysis."""

    def __init__(self, max_check_bytes: int = 256 * 1024):  # 256KB default cap
        super().__init__(max_check_bytes=max_check_bytes)
        self.analysis_byte_cap = max_check_bytes

    def detect_masquerade(
        self, content: bytes, declared_content_type: str, filename: str | None = None
    ) -> dict[str, Any]:
        """
        Detect masquerade with CPU-bounded analysis.

        Caps analysis to min(content_length, 256KB) to prevent CPU exhaustion
        on large files while maintaining detection accuracy.
        """
        if not content:
            return {
                "is_masquerade": False,
                "confidence": 0.0,
                "detected_type": None,
                "declared_type": declared_content_type,
                "filename": filename,
                "evidence": [],
                "analysis_bytes": 0,
                "total_bytes": 0,
                "byte_cap_applied": False,
            }

        # Apply byte cap
        total_bytes = len(content)
        analysis_bytes = min(total_bytes, self.analysis_byte_cap)
        byte_cap_applied = analysis_bytes < total_bytes

        # Analyze only the capped portion
        capped_content = content[:analysis_bytes]

        # Use parent detection logic on capped content
        result = super().detect_masquerade(
            capped_content, declared_content_type, filename
        )

        # Add byte cap metadata
        result.update(
            {
                "analysis_bytes": analysis_bytes,
                "total_bytes": total_bytes,
                "byte_cap_applied": byte_cap_applied,
                "analysis_percentage": (analysis_bytes / total_bytes * 100)
                if total_bytes > 0
                else 0,
            }
        )

        # Adjust confidence if byte cap was applied
        if byte_cap_applied and result["confidence"] > 0:
            # Slightly reduce confidence for partial analysis
            confidence_adjustment = 0.9  # 10% reduction for partial analysis
            result["confidence"] *= confidence_adjustment
            result["evidence"].append("partial_analysis_due_to_byte_cap")

        return result


def looks_binary_bounded(
    content: bytes,
    declared_content_type: str,
    filename: str | None = None,
    threshold: float = 0.6,
    max_analysis_bytes: int = 256 * 1024,
) -> bool:
    """
    CPU-bounded binary masquerade detection.

    Args:
        content: File content bytes
        declared_content_type: Declared MIME type
        filename: Optional filename
        threshold: Confidence threshold for binary detection
        max_analysis_bytes: Maximum bytes to analyze (default 256KB)

    Returns:
        True if content appears to be binary masquerading as text
    """
    detector = BoundedBinaryMasqueradeDetector(max_check_bytes=max_analysis_bytes)
    result = detector.detect_masquerade(content, declared_content_type, filename)
    return result["is_masquerade"] and result["confidence"] >= threshold


def test_masquerade_byte_cap():
    """Test masquerade detection with byte capping."""

    # Create test content larger than cap
    large_binary_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * (
        300 * 1024
    )  # 300KB PNG-like content
    large_text_content = b"This is normal text content. " * (10 * 1024)  # ~290KB text

    detector = BoundedBinaryMasqueradeDetector(max_check_bytes=256 * 1024)

    test_cases = [
        {
            "name": "large_binary_content",
            "content": large_binary_content,
            "declared_type": "text/plain",
            "filename": "fake.txt",
            "should_detect": True,
            "should_cap": True,
        },
        {
            "name": "large_text_content",
            "content": large_text_content,
            "declared_type": "text/plain",
            "filename": "document.txt",
            "should_detect": False,
            "should_cap": True,
        },
        {
            "name": "small_binary_content",
            "content": b"\x89PNG\r\n\x1a\n" + b"\x00" * 1000,  # 1KB
            "declared_type": "text/plain",
            "filename": "small.txt",
            "should_detect": True,
            "should_cap": False,
        },
    ]

    results = []

    for case in test_cases:
        result = detector.detect_masquerade(
            case["content"], case["declared_type"], case["filename"]
        )

        detection_correct = result["is_masquerade"] == case["should_detect"]
        cap_correct = result["byte_cap_applied"] == case["should_cap"]

        results.append(
            {
                "test_name": case["name"],
                "detection_correct": detection_correct,
                "cap_correct": cap_correct,
                "confidence": result["confidence"],
                "analysis_bytes": result["analysis_bytes"],
                "total_bytes": result["total_bytes"],
                "analysis_percentage": result["analysis_percentage"],
                "evidence": result["evidence"],
                "test_passed": detection_correct and cap_correct,
            }
        )

    # Test bounded function
    bounded_result = looks_binary_bounded(
        large_binary_content,
        "text/plain",
        "test.txt",
        max_analysis_bytes=128 * 1024,  # 128KB cap
    )

    return {
        "total_tests": len(test_cases),
        "passed_tests": sum(1 for r in results if r["test_passed"]),
        "test_results": results,
        "bounded_function_detected": bounded_result,
        "performance_summary": {
            "max_analysis_bytes": detector.analysis_byte_cap,
            "largest_file_tested": max(r["total_bytes"] for r in results),
            "cpu_bounded": True,
        },
    }


if __name__ == "__main__":
    # Run tests
    test_results = test_masquerade_byte_cap()

    print("Masquerade Byte Cap Test Results:")
    print(f"Passed: {test_results['passed_tests']}/{test_results['total_tests']}")

    for result in test_results["test_results"]:
        status = "✅" if result["test_passed"] else "❌"
        print(
            f"{status} {result['test_name']}: {result['analysis_percentage']:.1f}% analyzed, "
            f"confidence: {result['confidence']:.2f}"
        )

    print(
        f"\nBounded function detected masquerade: {test_results['bounded_function_detected']}"
    )
    print(f"Performance: {test_results['performance_summary']}")
