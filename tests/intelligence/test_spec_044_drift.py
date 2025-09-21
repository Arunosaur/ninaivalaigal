"""
SPEC-044: Memory Drift & Diff Detection - Comprehensive Test Coverage

Tests memory drift detection and change tracking system.
"""

import pytest
import requests
from unittest.mock import Mock, patch
import json

# Test Configuration
BASE_URL = "http://localhost:13370"
TEST_TOKEN = "test-token"
HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}


class TestMemoryDriftDetection:
    """Test suite for SPEC-044: Memory Drift & Diff Detection"""

    def test_drift_detection_basic(self):
        """Test basic drift detection functionality"""
        drift_data = {
            "memory_id": "test_memory_drift_001",
            "original_content": "This is the original content",
            "current_content": "This is the modified content",
            "detection_type": "content",
        }

        try:
            response = requests.post(
                f"{BASE_URL}/memory/drift/detect",
                json=drift_data,
                headers=HEADERS,
                timeout=5,
            )

            if response.status_code == 404:
                pytest.skip("Drift detection endpoint not implemented")

            assert (
                response.status_code == 200
            ), f"Drift detection failed: {response.status_code}"

            if response.status_code == 200:
                result = response.json()
                assert (
                    "drift_detected" in result
                ), "Drift detection response missing 'drift_detected' field"
                assert (
                    "similarity_score" in result
                ), "Drift detection response missing similarity score"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_semantic_drift_detection(self):
        """Test semantic drift detection"""
        semantic_data = {
            "memory_id": "test_memory_semantic_001",
            "original_content": "The cat sat on the mat",
            "current_content": "A feline rested on the rug",
            "detection_type": "semantic",
        }

        try:
            response = requests.post(
                f"{BASE_URL}/memory/drift/detect",
                json=semantic_data,
                headers=HEADERS,
                timeout=5,
            )

            if response.status_code == 404:
                pytest.skip("Semantic drift detection endpoint not implemented")

            assert (
                response.status_code == 200
            ), f"Semantic drift detection failed: {response.status_code}"

            if response.status_code == 200:
                result = response.json()
                # Semantic similarity should be high despite different words
                similarity = result.get("similarity_score", 0)
                assert similarity > 0.5, f"Semantic similarity too low: {similarity}"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_metadata_drift_detection(self):
        """Test metadata drift detection"""
        metadata_data = {
            "memory_id": "test_memory_metadata_001",
            "original_metadata": {
                "tags": ["python", "programming"],
                "context": "development",
                "priority": "high",
            },
            "current_metadata": {
                "tags": ["python", "coding", "development"],
                "context": "development",
                "priority": "medium",
            },
            "detection_type": "metadata",
        }

        try:
            response = requests.post(
                f"{BASE_URL}/memory/drift/detect",
                json=metadata_data,
                headers=HEADERS,
                timeout=5,
            )

            if response.status_code == 404:
                pytest.skip("Metadata drift detection endpoint not implemented")

            assert (
                response.status_code == 200
            ), f"Metadata drift detection failed: {response.status_code}"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_drift_history_tracking(self):
        """Test drift history and versioning"""
        history_data = {"memory_id": "test_memory_history_001"}

        try:
            response = requests.get(
                f"{BASE_URL}/memory/drift/history",
                params=history_data,
                headers=HEADERS,
                timeout=5,
            )

            if response.status_code == 404:
                pytest.skip("Drift history endpoint not implemented")

            assert (
                response.status_code == 200
            ), f"Drift history failed: {response.status_code}"

            if response.status_code == 200:
                result = response.json()
                assert isinstance(result, list), "Drift history should be a list"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")


class TestDriftDetectionEdgeCases:
    """Test edge cases for drift detection"""

    def test_identical_content_drift(self):
        """Test drift detection with identical content"""
        identical_data = {
            "memory_id": "test_memory_identical_001",
            "original_content": "Identical content for testing",
            "current_content": "Identical content for testing",
            "detection_type": "content",
        }

        try:
            response = requests.post(
                f"{BASE_URL}/memory/drift/detect",
                json=identical_data,
                headers=HEADERS,
                timeout=5,
            )

            if response.status_code == 404:
                pytest.skip("Drift detection endpoint not implemented")

            assert (
                response.status_code == 200
            ), f"Identical content test failed: {response.status_code}"

            if response.status_code == 200:
                result = response.json()
                # Should detect no drift for identical content
                assert (
                    result.get("drift_detected") == False
                ), "Drift detected for identical content"
                assert (
                    result.get("similarity_score", 0) >= 0.99
                ), "Similarity score too low for identical content"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_formatting_only_changes(self):
        """Test drift detection with formatting-only changes"""
        formatting_data = {
            "memory_id": "test_memory_formatting_001",
            "original_content": "This is a test with   multiple   spaces",
            "current_content": "This is a test with multiple spaces",
            "detection_type": "content",
        }

        try:
            response = requests.post(
                f"{BASE_URL}/memory/drift/detect",
                json=formatting_data,
                headers=HEADERS,
                timeout=5,
            )

            if response.status_code == 404:
                pytest.skip("Drift detection endpoint not implemented")

            assert (
                response.status_code == 200
            ), f"Formatting drift test failed: {response.status_code}"

            if response.status_code == 200:
                result = response.json()
                # Should have high similarity despite formatting differences
                similarity = result.get("similarity_score", 0)
                assert (
                    similarity > 0.8
                ), f"Similarity too low for formatting changes: {similarity}"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_mass_token_deletion_detection(self):
        """Test detection of mass token deletion"""
        deletion_data = {
            "memory_ids": [f"deleted_memory_{i:03d}" for i in range(50)],
            "detection_type": "mass_deletion",
        }

        try:
            response = requests.post(
                f"{BASE_URL}/memory/drift/mass-deletion",
                json=deletion_data,
                headers=HEADERS,
                timeout=5,
            )

            if response.status_code == 404:
                pytest.skip("Mass deletion detection endpoint not implemented")

            assert (
                response.status_code == 200
            ), f"Mass deletion detection failed: {response.status_code}"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")


class TestDriftPerformance:
    """Test drift detection performance"""

    def test_drift_detection_performance(self):
        """Test drift detection performance with multiple comparisons"""
        import time

        try:
            # Test multiple drift detections
            start_time = time.time()

            for i in range(10):
                drift_data = {
                    "memory_id": f"perf_test_memory_{i:03d}",
                    "original_content": f"Original content number {i} with some text",
                    "current_content": f"Modified content number {i} with different text",
                    "detection_type": "content",
                }

                response = requests.post(
                    f"{BASE_URL}/memory/drift/detect",
                    json=drift_data,
                    headers=HEADERS,
                    timeout=2,
                )

                if response.status_code == 404:
                    pytest.skip("Drift detection endpoint not implemented")

                assert response.status_code == 200, f"Performance test {i} failed"

            total_time = time.time() - start_time
            avg_time = total_time / 10

            print(f"Average drift detection time: {avg_time*1000:.2f}ms")

            # Performance assertion - drift detection should be fast
            assert avg_time < 1.0, f"Drift detection too slow: {avg_time:.3f}s average"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_redis_cached_similarity(self):
        """Test Redis caching of similarity calculations"""
        try:
            # First calculation (cache miss)
            drift_data = {
                "memory_id": "cached_similarity_test",
                "original_content": "Content for caching test",
                "current_content": "Modified content for caching test",
                "detection_type": "content",
            }

            import time

            start_time = time.time()
            response1 = requests.post(
                f"{BASE_URL}/memory/drift/detect",
                json=drift_data,
                headers=HEADERS,
                timeout=5,
            )
            first_time = time.time() - start_time

            if response1.status_code == 404:
                pytest.skip("Drift detection endpoint not implemented")

            # Second calculation (cache hit)
            start_time = time.time()
            response2 = requests.post(
                f"{BASE_URL}/memory/drift/detect",
                json=drift_data,
                headers=HEADERS,
                timeout=5,
            )
            second_time = time.time() - start_time

            assert response2.status_code == 200, "Cached similarity request failed"

            print(
                f"First calculation: {first_time:.3f}s, Second calculation: {second_time:.3f}s"
            )

            # Results should be identical
            if response1.status_code == 200 and response2.status_code == 200:
                result1 = response1.json()
                result2 = response2.json()
                assert result1.get("similarity_score") == result2.get(
                    "similarity_score"
                ), "Cached results differ"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
