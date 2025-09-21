"""
Test suite for P0 multipart hardening patch.

Tests critical security enhancements:
- Mach-O and Java class magic detection
- MP4/ISO-BMFF offset detection
- Archive blocking for text endpoints
- UTF-8 only policy for text parts
- Content-Transfer-Encoding guard
- Stream-time per-part limit enforcement
"""

import pytest

from server.security.multipart.strict_limits_hardened import (
    HardenedPartLimitConfig,
    StreamLimitState,
    _looks_binary_enhanced,
    create_hardened_config,
    detect_enhanced_magic_bytes,
    detect_mp4_iso_bmff,
    disallow_archives_for_text,
    enforce_max_parts_per_request,
    enforce_part_limits_buffer,
    enforce_part_limits_stream,
    reject_content_transfer_encoding,
    require_utf8_text,
)


class TestMachoAndJavaDetection:
    """Test P0: Mach-O and Java class magic detection."""

    def test_macho_32bit_detection(self):
        """Test Mach-O 32-bit executable detection."""
        macho_content = b"\xcf\xfa\xed\xfe" + b"fake_macho_data" * 50
        result = detect_enhanced_magic_bytes(macho_content)

        assert result["detected"] is True
        assert result["detected_type"] == "application/x-mach-binary"
        assert result["is_executable"] is True
        assert result["confidence"] == 0.95

    def test_macho_64bit_detection(self):
        """Test Mach-O 64-bit executable detection."""
        macho_content = b"\xcf\xfa\xed\xfe" + b"fake_macho64_data" * 50
        result = detect_enhanced_magic_bytes(macho_content)

        assert result["detected"] is True
        assert result["detected_type"] == "application/x-mach-binary"
        assert result["is_executable"] is True

    def test_java_class_detection(self):
        """Test Java class file detection."""
        java_content = b"\xca\xfe\xba\xbe" + b"\x00\x34" + b"fake_class_data" * 50
        result = detect_enhanced_magic_bytes(java_content)

        assert result["detected"] is True
        assert result["detected_type"] == "application/java-vm"
        assert result["is_executable"] is True
        assert result["confidence"] == 0.95

    def test_macho_java_blocking(self):
        """Test that Mach-O and Java are blocked as executables."""
        config = HardenedPartLimitConfig(block_executable_magic_bytes=True)

        # Mach-O should be blocked
        macho_content = b"\xcf\xfa\xed\xfe" + b"fake_macho" * 100
        result = enforce_part_limits_buffer(macho_content, "application/octet-stream", config=config)

        assert result["valid"] is False
        assert any(v["type"] == "executable_blocked" for v in result["violations"])

        # Java class should be blocked
        java_content = b"\xca\xfe\xba\xbe" + b"fake_class" * 100
        result = enforce_part_limits_buffer(java_content, "application/octet-stream", config=config)

        assert result["valid"] is False
        assert any(v["type"] == "executable_blocked" for v in result["violations"])


class TestMP4OffsetDetection:
    """Test P0: MP4/ISO-BMFF detection via ftyp within first 12 bytes."""

    def test_mp4_ftyp_at_offset_4(self):
        """Test MP4 detection with ftyp at standard offset 4."""
        mp4_content = b"\x00\x00\x00\x18ftypisom\x00\x00" + b"fake_mp4_data" * 100

        assert detect_mp4_iso_bmff(mp4_content) is True

        result = detect_enhanced_magic_bytes(mp4_content)
        assert result["detected"] is True
        assert result["detected_type"] == "video/mp4"
        assert result["is_executable"] is False
        assert result["confidence"] == 0.90

    def test_mp4_ftyp_at_different_offset(self):
        """Test MP4 detection with ftyp at different offset within scan window."""
        mp4_content = b"\x00\x00\x00\x20\x00\x00\x00\x14ftypmp41" + b"fake_data" * 50

        assert detect_mp4_iso_bmff(mp4_content) is True

        result = detect_enhanced_magic_bytes(mp4_content)
        assert result["detected"] is True
        assert result["detected_type"] == "video/mp4"

    def test_no_mp4_detection_without_ftyp(self):
        """Test that content without ftyp is not detected as MP4."""
        non_mp4_content = b"\x00\x00\x00\x18notmp4data\x00\x00" + b"fake_data" * 100

        assert detect_mp4_iso_bmff(non_mp4_content) is False

        result = detect_enhanced_magic_bytes(non_mp4_content)
        assert result["detected"] is False

    def test_mp4_too_short(self):
        """Test MP4 detection with content too short."""
        short_content = b"\x00\x00\x00"

        assert detect_mp4_iso_bmff(short_content) is False


class TestArchiveBlockingForText:
    """Test P0: Archive blocking for text-only endpoints."""

    def test_zip_blocked_for_text_endpoint(self):
        """Test ZIP archive blocked when declared as text."""
        magic_result = {
            "detected": True,
            "detected_type": "application/zip",
            "is_archive": True
        }

        result = disallow_archives_for_text(magic_result, "text/plain")

        assert result["valid"] is False
        assert any(v["type"] == "archive_blocked_for_text" for v in result["violations"])

    def test_gzip_blocked_for_json_endpoint(self):
        """Test GZIP archive blocked for JSON endpoint."""
        magic_result = {
            "detected": True,
            "detected_type": "application/gzip",
            "is_archive": True
        }

        result = disallow_archives_for_text(magic_result, "application/json")

        assert result["valid"] is False
        assert any(v["type"] == "archive_blocked_for_text" for v in result["violations"])

    def test_archive_allowed_for_binary_endpoint(self):
        """Test archive allowed for binary endpoint."""
        magic_result = {
            "detected": True,
            "detected_type": "application/zip",
            "is_archive": True
        }

        result = disallow_archives_for_text(magic_result, "application/octet-stream")

        assert result["valid"] is True
        assert len(result["violations"]) == 0

    def test_integrated_archive_blocking(self):
        """Test integrated archive blocking in buffer limits."""
        config = HardenedPartLimitConfig(block_archives_for_text=True)

        # ZIP content declared as text should be blocked
        zip_content = b"PK\x03\x04" + b"fake_zip_data" * 100
        result = enforce_part_limits_buffer(zip_content, "text/plain", config=config)

        assert result["valid"] is False
        assert any(v["type"] == "archive_blocked_for_text" for v in result["violations"])


class TestUTF8OnlyPolicy:
    """Test P0: UTF-8 only policy for text parts."""

    def test_valid_utf8_text(self):
        """Test valid UTF-8 text passes validation."""
        utf8_content = "Hello, 世界! 🌍".encode()
        result = require_utf8_text(utf8_content)

        assert result["valid"] is True
        assert result["encoding"] == "utf-8"
        assert len(result["violations"]) == 0

    def test_utf16_bom_rejected(self):
        """Test UTF-16 BOM is rejected."""
        utf16_content = "hello".encode('utf-16')
        result = require_utf8_text(utf16_content)

        assert result["valid"] is False
        assert result["encoding"] == "utf-16"
        assert any(v["type"] == "utf16_bom_detected" for v in result["violations"])

    def test_invalid_utf8_rejected(self):
        """Test invalid UTF-8 bytes are rejected."""
        invalid_utf8 = b"\xff\xfe\x00\x48\x00\x65\x00\x6c\x00\x6c\x00\x6f"  # UTF-16 content
        result = require_utf8_text(invalid_utf8)

        assert result["valid"] is False
        assert result["encoding"] == "utf-16"  # Correctly detected as UTF-16
        assert any(v["type"] == "utf16_bom_detected" for v in result["violations"])

    def test_truly_invalid_utf8_rejected(self):
        """Test truly invalid UTF-8 bytes are rejected."""
        # Invalid UTF-8 sequence without BOM
        invalid_utf8 = b"Hello \x80\x81\x82 world"  # Invalid continuation bytes
        result = require_utf8_text(invalid_utf8)

        assert result["valid"] is False
        assert result["encoding"] == "unknown"
        assert any(v["type"] == "invalid_utf8" for v in result["violations"])

    def test_integrated_utf8_validation(self):
        """Test integrated UTF-8 validation in buffer limits."""
        config = HardenedPartLimitConfig(require_utf8_text=True)

        # UTF-16 content should be rejected for text parts
        utf16_content = "hello world".encode('utf-16')
        result = enforce_part_limits_buffer(utf16_content, "text/plain", config=config)

        assert result["valid"] is False
        assert any(v["type"] == "utf16_bom_detected" for v in result["violations"])

    def test_integrated_invalid_utf8_validation(self):
        """Test integrated invalid UTF-8 validation in buffer limits."""
        config = HardenedPartLimitConfig(require_utf8_text=True)

        # Invalid UTF-8 content should be rejected for text parts
        invalid_utf8 = b"Hello \x80\x81\x82 world"  # Invalid continuation bytes
        result = enforce_part_limits_buffer(invalid_utf8, "text/plain", config=config)

        assert result["valid"] is False
        assert any(v["type"] == "invalid_utf8" for v in result["violations"])


class TestContentTransferEncodingGuard:
    """Test P0: Content-Transfer-Encoding guard."""

    def test_base64_encoding_rejected(self):
        """Test base64 encoding is rejected."""
        result = reject_content_transfer_encoding("base64")

        assert result["valid"] is False
        assert any(v["type"] == "blocked_content_transfer_encoding" for v in result["violations"])
        assert any(v["encoding"] == "base64" for v in result["violations"])

    def test_quoted_printable_rejected(self):
        """Test quoted-printable encoding is rejected."""
        result = reject_content_transfer_encoding("quoted-printable")

        assert result["valid"] is False
        assert any(v["type"] == "blocked_content_transfer_encoding" for v in result["violations"])

    def test_7bit_8bit_rejected(self):
        """Test 7bit and 8bit encodings are rejected."""
        result_7bit = reject_content_transfer_encoding("7bit")
        result_8bit = reject_content_transfer_encoding("8bit")

        assert result_7bit["valid"] is False
        assert result_8bit["valid"] is False

    def test_no_encoding_header_allowed(self):
        """Test missing encoding header is allowed."""
        result = reject_content_transfer_encoding(None)

        assert result["valid"] is True
        assert len(result["violations"]) == 0

    def test_integrated_cte_validation(self):
        """Test integrated CTE validation in buffer limits."""
        config = HardenedPartLimitConfig(reject_content_transfer_encoding=True)

        # base64 CTE should be rejected for text parts
        text_content = b"Hello, world!"
        result = enforce_part_limits_buffer(
            text_content,
            "text/plain",
            config=config,
            cte_header="base64"
        )

        assert result["valid"] is False
        assert any(v["type"] == "blocked_content_transfer_encoding" for v in result["violations"])


class TestStreamTimeLimitEnforcement:
    """Test P0: Stream-time per-part limit enforcement."""

    def test_stream_limit_enforcement(self):
        """Test stream-time limit enforcement aborts early."""
        config = HardenedPartLimitConfig(max_part_bytes=1000)
        state = StreamLimitState(part_number=1)

        # First chunk within limit
        result1 = enforce_part_limits_stream(state, 500, config)
        assert result1["valid"] is True
        assert result1["should_abort"] is False
        assert result1["bytes_seen"] == 500

        # Second chunk exceeds limit
        result2 = enforce_part_limits_stream(state, 600, config)
        assert result2["valid"] is False
        assert result2["should_abort"] is True
        assert result2["bytes_seen"] == 1100
        assert state.limit_exceeded is True

    def test_stream_state_tracking(self):
        """Test stream state is properly tracked."""
        config = HardenedPartLimitConfig(max_part_bytes=2000)
        state = StreamLimitState(part_number=2)

        # Multiple chunks within limit
        chunks = [300, 400, 500, 600]  # Total: 1800 bytes

        for chunk_size in chunks:
            result = enforce_part_limits_stream(state, chunk_size, config)
            assert result["valid"] is True
            assert result["should_abort"] is False

        assert state.bytes_seen == 1800
        assert state.limit_exceeded is False

    def test_stream_violation_details(self):
        """Test stream violation includes detailed information."""
        config = HardenedPartLimitConfig(max_part_bytes=100)
        state = StreamLimitState(part_number=5)

        result = enforce_part_limits_stream(state, 150, config)

        assert result["valid"] is False
        violation = result["violations"][0]
        assert violation["type"] == "stream_part_limit_exceeded"
        assert violation["severity"] == "critical"
        assert violation["bytes_seen"] == 150
        assert violation["limit"] == 100
        assert "Part 5" in violation["message"]


class TestPartCountDoSPrevention:
    """Test P0: Part count DoS prevention."""

    def test_max_parts_enforcement(self):
        """Test maximum parts per request enforcement."""
        config = HardenedPartLimitConfig(max_parts_per_request=256)

        # Within limit
        result_ok = enforce_max_parts_per_request(200, config)
        assert result_ok["valid"] is True
        assert len(result_ok["violations"]) == 0

        # Exceeds limit
        result_fail = enforce_max_parts_per_request(300, config)
        assert result_fail["valid"] is False
        assert any(v["type"] == "too_many_parts" for v in result_fail["violations"])

    def test_part_count_violation_details(self):
        """Test part count violation includes details."""
        config = HardenedPartLimitConfig(max_parts_per_request=100)

        result = enforce_max_parts_per_request(150, config)

        violation = result["violations"][0]
        assert violation["part_count"] == 150
        assert violation["limit"] == 100
        assert violation["severity"] == "high"


class TestHardenedConfiguration:
    """Test hardened configuration creation."""

    def test_text_only_endpoint_config(self):
        """Test configuration for text-only endpoints."""
        config = create_hardened_config(text_only_endpoint=True)

        assert config.block_archives_for_text is True
        assert config.require_utf8_text is True
        assert config.reject_content_transfer_encoding is True
        assert config.block_executable_magic_bytes is True

    def test_binary_endpoint_config(self):
        """Test configuration for binary endpoints."""
        config = create_hardened_config(text_only_endpoint=False)

        assert config.block_archives_for_text is False
        assert config.require_utf8_text is False
        assert config.reject_content_transfer_encoding is False
        assert config.block_executable_magic_bytes is True  # Always block executables

    def test_custom_upload_size(self):
        """Test custom upload size configuration."""
        config = create_hardened_config(max_upload_size=5 * 1024 * 1024)  # 5MB

        assert config.max_part_bytes == 5 * 1024 * 1024
        assert config.max_binary_part_bytes == 5 * 1024 * 1024
        assert config.max_text_part_bytes == 1 * 1024 * 1024  # Capped at 1MB


class TestIntegrationScenarios:
    """Test integrated scenarios with multiple P0 features."""

    def test_malicious_macho_upload(self):
        """Test malicious Mach-O upload is blocked."""
        config = create_hardened_config(text_only_endpoint=True)

        # Mach-O binary disguised as text
        macho_content = b"\xcf\xfa\xed\xfe" + b"malicious_payload" * 100
        result = enforce_part_limits_buffer(
            macho_content,
            "text/plain",
            "innocent.txt",
            config
        )

        assert result["valid"] is False
        # Should be blocked for multiple reasons
        violation_types = [v["type"] for v in result["violations"]]
        assert "executable_blocked" in violation_types

    def test_base64_encoded_archive_bypass_attempt(self):
        """Test base64-encoded archive bypass attempt is blocked."""
        config = create_hardened_config(text_only_endpoint=True)

        # Attempt to bypass with base64 encoding
        text_content = b"This looks like innocent text content"
        result = enforce_part_limits_buffer(
            text_content,
            "text/plain",
            "data.txt",
            config,
            cte_header="base64"
        )

        assert result["valid"] is False
        assert any(v["type"] == "blocked_content_transfer_encoding" for v in result["violations"])

    def test_comprehensive_validation_pass(self):
        """Test legitimate upload passes all validations."""
        config = create_hardened_config(text_only_endpoint=True)

        # Legitimate UTF-8 text content
        text_content = b"Hello, world! This is valid UTF-8 text."
        result = enforce_part_limits_buffer(
            text_content,
            "text/plain",
            "document.txt",
            config
        )

        assert result["valid"] is True
        assert len(result["violations"]) == 0
        assert result["is_binary"] is False


def test_enhanced_binary_detection():
    """Test enhanced binary detection with P0 features."""
    # Mach-O should be detected as binary
    assert _looks_binary_enhanced(b"\xcf\xfa\xed\xfe" + b"data") is True

    # Java class should be detected as binary
    assert _looks_binary_enhanced(b"\xca\xfe\xba\xbe" + b"data") is True

    # MP4 should be detected as binary
    assert _looks_binary_enhanced(b"\x00\x00\x00\x18ftypisom") is True

    # Regular text should not be detected as binary
    assert _looks_binary_enhanced(b"Hello, world!") is False


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
