"""
Entropy Calculation Utilities

Shannon entropy calculation for detecting high-entropy strings that may be secrets.
"""

import math
from collections import Counter


class EntropyCalculator:
    """Calculate Shannon entropy for secret detection"""

    @staticmethod
    def calculate_shannon_entropy(text: str) -> float:
        """
        Calculate Shannon entropy of a string.

        Args:
            text: Input string to analyze

        Returns:
            Shannon entropy value (higher = more random/likely secret)
        """
        if not text:
            return 0.0

        # Count character frequencies
        char_counts = Counter(text)
        text_length = len(text)

        # Calculate entropy
        entropy = 0.0
        for count in char_counts.values():
            probability = count / text_length
            if probability > 0:
                entropy -= probability * math.log2(probability)

        return entropy

    @staticmethod
    def calculate_base64_entropy(text: str) -> float:
        """
        Calculate entropy specifically for base64-like strings.

        Args:
            text: Input string to analyze

        Returns:
            Adjusted entropy for base64 character set
        """
        if not text:
            return 0.0

        # Base64 character set
        base64_chars = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
        )

        # Filter to only base64 characters
        filtered_text = "".join(c for c in text if c in base64_chars)

        if not filtered_text:
            return 0.0

        return EntropyCalculator.calculate_shannon_entropy(filtered_text)

    @staticmethod
    def calculate_hex_entropy(text: str) -> float:
        """
        Calculate entropy for hexadecimal strings.

        Args:
            text: Input string to analyze

        Returns:
            Adjusted entropy for hex character set
        """
        if not text:
            return 0.0

        # Hex character set
        hex_chars = set("0123456789abcdefABCDEF")

        # Filter to only hex characters
        filtered_text = "".join(c for c in text if c in hex_chars)

        if not filtered_text:
            return 0.0

        return EntropyCalculator.calculate_shannon_entropy(filtered_text)

    @staticmethod
    def get_entropy_metrics(text: str) -> dict[str, float]:
        """
        Get comprehensive entropy metrics for a string.

        Args:
            text: Input string to analyze

        Returns:
            Dictionary with various entropy measurements
        """
        return {
            "shannon_entropy": EntropyCalculator.calculate_shannon_entropy(text),
            "base64_entropy": EntropyCalculator.calculate_base64_entropy(text),
            "hex_entropy": EntropyCalculator.calculate_hex_entropy(text),
            "length": len(text),
            "unique_chars": len(set(text)),
            "char_diversity": len(set(text)) / len(text) if text else 0.0,
        }


# Convenience function for backward compatibility
def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy of a string"""
    return EntropyCalculator.calculate_shannon_entropy(text)
