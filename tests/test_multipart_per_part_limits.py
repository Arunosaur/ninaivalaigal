"""
Test suite for multipart per-part limits with PE/PDF/PNG magic byte checks.

Tests the enhanced multipart validation system with:
- Per-part size limits (text vs binary)
- Magic byte detection for PE/PDF/PNG and other formats
- Executable content blocking
- Content-type vs magic byte mismatch detection
- Integration with strict multipart validator
"""

import pytest

from server.security.multipart.strict_limits import (
    PartLimitConfig,
    detect_magic_bytes,
    enforce_part_limits,
    looks_binary,
)
from server.security.multipart.strict_validator import (
    StrictMultipartValidator,
    create_permissive_policy,
    create_strict_policy,
)


class TestMagicByteDetection:
    """Test magic byte detection functionality."""

    def test_pe_executable_detection(self):
        """Test PE executable magic byte detection."""
        pe_content = b"MZ" + b"\x90\x00" + b"fake_pe_data" * 100
        result = detect_magic_bytes(pe_content)

        assert result.detected is True
        assert result.detected_type == "application/x-msdownload"
        assert result.is_executable is True
        assert result.confidence == 0.95
        assert result.signature == b"MZ"

    def test_pdf_detection(self):
        """Test PDF magic byte detection."""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog" + b"\x00" * 100
        result = detect_magic_bytes(pdf_content)

        assert result.detected is True
        assert result.detected_type == "application/pdf"
        assert result.is_executable is False
        assert result.confidence == 0.95
        assert result.signature == b"%PDF"

    def test_png_detection(self):
        """Test PNG magic byte detection."""
        png_content = b"\x89PNG\r\n\x1a\n" + b"fake_png_data" * 50
        result = detect_magic_bytes(png_content)

        assert result.detected is True
        assert result.detected_type == "image/png"
        assert result.is_executable is False
        assert result.confidence == 0.95
        assert result.signature == b"\x89PNG\r\n\x1a\n"

    def test_elf_executable_detection(self):
        """Test ELF executable detection."""
        elf_content = b"\x7fELF" + b"\x01\x01\x01\x00" + b"fake_elf_data" * 100
        result = detect_magic_bytes(elf_content)

        assert result.detected is True
        assert result.detected_type == "application/x-executable"
        assert result.is_executable is True
        assert result.confidence == 0.95

    def test_no_magic_bytes(self):
        """Test content with no magic bytes."""
        text_content = b"This is just plain text content with no magic bytes"
        result = detect_magic_bytes(text_content)

        assert result.detected is False
        assert result.detected_type is None
        assert result.is_executable is False
        assert result.confidence == 0.0
        assert result.signature is None

    def test_empty_content(self):
        """Test empty content."""
        result = detect_magic_bytes(b"")

        assert result.detected is False
        assert result.detected_type is None
        assert result.is_executable is False
        assert result.confidence == 0.0


class TestPartLimitEnforcement:
    """Test per-part limit enforcement."""

    def test_basic_size_limit_enforcement(self):
        """Test basic size limit enforcement."""
        config = PartLimitConfig(max_part_bytes=1000)

        # Content within limit
        small_content = b"x" * 500
        result = enforce_part_limits(small_content, "text/plain", config=config)
        assert result["valid"] is True
        assert result["size_bytes"] == 500

        # Content exceeding limit
        large_content = b"x" * 1500
        with pytest.raises(ValueError, match="multipart part exceeds per-part limit"):
            enforce_part_limits(large_content, "text/plain", config=config)

    def test_text_vs_binary_size_limits(self):
        """Test different size limits for text vs binary content."""
        config = PartLimitConfig(
            max_text_part_bytes=1000,
            max_binary_part_bytes=5000
        )

        # Text content within text limit
        text_content = b"Plain text content" * 30  # ~540 bytes
        result = enforce_part_limits(text_content, "text/plain", config=config)
        assert result["valid"] is True
        assert result["is_binary"] is False

        # Binary content within binary limit
        png_content = b"\x89PNG\r\n\x1a\n" + b"x" * 3000  # ~3008 bytes
        result = enforce_part_limits(png_content, "image/png", config=config)
        assert result["valid"] is True
        assert result["is_binary"] is True

        # Text content exceeding text limit but within binary limit
        large_text = b"x" * 2000
        with pytest.raises(ValueError, match="Text part exceeds size limit"):
            enforce_part_limits(large_text, "text/plain", config=config)

    def test_executable_blocking(self):
        """Test blocking of executable content."""
        config = PartLimitConfig(block_executable_magic_bytes=True)

        # PE executable should be blocked
        pe_content = b"MZ" + b"\x90\x00" + b"fake_pe_data" * 100
        with pytest.raises(ValueError, match="Executable content blocked"):
            enforce_part_limits(pe_content, "application/octet-stream", config=config)

        # ELF executable should be blocked
        elf_content = b"\x7fELF" + b"\x01\x01\x01\x00" + b"fake_elf_data" * 100
        with pytest.raises(ValueError, match="Executable content blocked"):
            enforce_part_limits(elf_content, "application/octet-stream", config=config)

        # Non-executable should pass
        pdf_content = b"%PDF-1.4\nfake pdf content"
        result = enforce_part_limits(pdf_content, "application/pdf", config=config)
        assert result["valid"] is True

    def test_content_type_magic_mismatch(self):
        """Test detection of content-type vs magic byte mismatches."""
        config = PartLimitConfig(enforce_magic_byte_checks=True)

        # PNG content declared as text should trigger warning
        png_content = b"\x89PNG\r\n\x1a\n" + b"fake_png_data" * 50
        result = enforce_part_limits(png_content, "text/plain", config=config)

        # Should not fail validation but should log warning
        assert result["valid"] is True
        assert len(result["violations"]) > 0
        assert any(v["type"] == "content_type_magic_mismatch" for v in result["violations"])

        # Correct content-type should not trigger warning
        result = enforce_part_limits(png_content, "image/png", config=config)
        assert result["valid"] is True
        assert len([v for v in result["violations"] if v["type"] == "content_type_magic_mismatch"]) == 0

    def test_disable_magic_byte_checks(self):
        """Test disabling magic byte checks."""
        config = PartLimitConfig(enforce_magic_byte_checks=False)

        # PE executable should not be blocked when checks disabled
        pe_content = b"MZ" + b"\x90\x00" + b"fake_pe_data" * 100
        result = enforce_part_limits(pe_content, "text/plain", config=config)
        assert result["valid"] is True
        assert result["magic_byte_result"] is None


class TestBinaryDetection:
    """Test enhanced binary content detection."""

    def test_null_byte_detection(self):
        """Test null byte detection for binary content."""
        content_with_nulls = b"text\x00\x00binary\x00content"
        assert looks_binary(content_with_nulls) is True

        text_content = b"This is plain text without null bytes"
        assert looks_binary(text_content) is False

    def test_magic_byte_binary_detection(self):
        """Test magic byte based binary detection."""
        png_content = b"\x89PNG\r\n\x1a\n" + b"fake_png_data"
        assert looks_binary(png_content) is True

        pdf_content = b"%PDF-1.4\nfake pdf content"
        assert looks_binary(pdf_content) is True

        text_content = b"Regular text content"
        assert looks_binary(text_content) is False

    def test_printable_ratio_detection(self):
        """Test printable character ratio for binary detection."""
        # High ratio of non-printable characters
        binary_like = bytes(range(0, 255, 3)) * 10  # Lots of control chars
        assert looks_binary(binary_like) is True

        # Mostly printable characters
        mostly_text = b"Hello world! 123 ABC xyz" * 10
        assert looks_binary(mostly_text) is False


class TestStrictValidatorIntegration:
    """Test integration with StrictMultipartValidator."""

    def test_validator_with_content_limits(self):
        """Test validator integration with content and limits."""
        validator = StrictMultipartValidator()
        config = PartLimitConfig(max_text_part_bytes=1000)

        # Valid text content
        text_content = b"Valid text content" * 20
        result = validator.validate_part(
            "text_field",
            "text/plain",
            "document.txt",
            text_content,
            config
        )

        assert result["valid"] is True
        assert result["size_bytes"] == len(text_content)
        assert result["is_binary"] is False

        # Oversized text content
        large_text = b"x" * 2000
        result = validator.validate_part(
            "large_field",
            "text/plain",
            "large.txt",
            large_text,
            config
        )

        assert result["valid"] is False
        assert "part_limit_exceeded" in result["violations"]
        assert "limit_error" in result

    def test_validator_executable_blocking(self):
        """Test validator blocks executable content."""
        validator = StrictMultipartValidator()
        config = PartLimitConfig(block_executable_magic_bytes=True)

        # PE executable should be blocked
        pe_content = b"MZ" + b"\x90\x00" + b"fake_pe_data" * 100
        result = validator.validate_part(
            "exe_field",
            "application/octet-stream",
            "malware.exe",
            pe_content,
            config
        )

        assert result["valid"] is False
        assert "part_limit_exceeded" in result["violations"]
        assert "Executable content blocked" in result["limit_error"]

    def test_validator_magic_byte_metadata(self):
        """Test validator includes magic byte metadata."""
        validator = StrictMultipartValidator()

        # PNG content
        png_content = b"\x89PNG\r\n\x1a\n" + b"fake_png_data" * 50
        result = validator.validate_part(
            "image_field",
            "image/png",
            "image.png",
            png_content
        )

        assert result["valid"] is True
        assert result["magic_byte_result"] is not None
        assert result["magic_byte_result"].detected is True
        assert result["magic_byte_result"].detected_type == "image/png"
        assert result["is_binary"] is True


class TestPolicyConfigurations:
    """Test different policy configurations."""

    def test_strict_policy_creation(self):
        """Test strict policy creation."""
        policy = create_strict_policy(allow_binary=False)

        assert len(policy.allowed_binary_types) == 0
        assert policy.require_content_type_match is True
        assert policy.block_executable_extensions is True
        assert policy.max_parts == 50

        # With binary allowed
        policy_with_binary = create_strict_policy(allow_binary=True)
        assert len(policy_with_binary.allowed_binary_types) > 0

    def test_permissive_policy_creation(self):
        """Test permissive policy creation."""
        policy = create_permissive_policy()

        assert len(policy.allowed_text_types) > len(StrictMultipartValidator.DEFAULT_TEXT_TYPES)
        assert len(policy.allowed_binary_types) > len(StrictMultipartValidator.DEFAULT_BINARY_TYPES)
        assert policy.require_content_type_match is False
        assert policy.max_parts == 100


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_content_handling(self):
        """Test handling of empty content."""
        result = enforce_part_limits(b"", "text/plain")
        assert result["valid"] is True
        assert result["size_bytes"] == 0
        assert result["is_binary"] is False

    def test_large_magic_byte_check(self):
        """Test magic byte detection with large content."""
        # Large content with magic bytes at start
        large_png = b"\x89PNG\r\n\x1a\n" + b"x" * 100000
        result = detect_magic_bytes(large_png, max_check_bytes=512)

        assert result.detected is True
        assert result.detected_type == "image/png"
        # Should only check first 512 bytes for efficiency

    def test_multiple_violations(self):
        """Test content with multiple violations."""
        config = PartLimitConfig(
            max_part_bytes=1000,
            block_executable_magic_bytes=True
        )

        # Large PE executable (multiple violations)
        large_pe = b"MZ" + b"x" * 2000
        with pytest.raises(ValueError) as exc_info:
            enforce_part_limits(large_pe, "text/plain", config=config)

        # Should fail on first violation (size limit)
        assert "multipart part exceeds per-part limit" in str(exc_info.value)


def test_comprehensive_multipart_validation():
    """Comprehensive test of multipart validation with various content types."""
    validator = StrictMultipartValidator()
    config = PartLimitConfig(
        max_text_part_bytes=2000,
        max_binary_part_bytes=10000,
        block_executable_magic_bytes=True
    )

    parts = [
        {
            "field_name": "text_field",
            "content_type": "text/plain",
            "filename": "document.txt",
            "content": b"Valid text document content" * 30
        },
        {
            "field_name": "image_field",
            "content_type": "image/png",
            "filename": "image.png",
            "content": b"\x89PNG\r\n\x1a\n" + b"fake_png_data" * 100
        },
        {
            "field_name": "pdf_field",
            "content_type": "application/pdf",
            "filename": "document.pdf",
            "content": b"%PDF-1.4\nfake pdf content" * 50
        }
    ]

    result = validator.validate_multipart_request(parts, config)

    assert result["valid"] is True
    assert result["total_parts"] == 3
    assert result["summary"]["text_parts"] == 1
    assert result["summary"]["binary_parts"] == 2
    assert result["summary"]["invalid_parts"] == 0

    # Check individual part results
    for part_result in result["part_results"]:
        assert part_result["valid"] is True
        assert "size_bytes" in part_result
        assert "magic_byte_result" in part_result


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
