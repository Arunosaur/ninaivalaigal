"""Tests for filename sanitization utilities."""

import pytest

from server.utils.filename_sanitizer import (
    is_archive_extension,
    normalize_content_disposition_filename,
    sanitize_filename,
    validate_filename_safety,
)


class TestSanitizeFilename:
    """Test filename sanitization functionality."""

    def test_basic_sanitization(self):
        """Test basic filename sanitization."""
        assert sanitize_filename("hello world.txt") == "hello_world.txt"
        assert sanitize_filename("file@#$%.doc") == "file____.doc"
        assert sanitize_filename("normal_file-123.pdf") == "normal_file-123.pdf"

    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        # Test NFC normalization
        filename = "café.txt"  # é as combining characters
        result = sanitize_filename(filename)
        assert "cafe" in result.lower() or "café" in result

    def test_path_traversal_prevention(self):
        """Test path traversal prevention."""
        assert sanitize_filename("../../../etc/passwd") == "_._._etc_passwd"
        assert sanitize_filename("..\\windows\\system32") == "_windows_system32"
        assert sanitize_filename("file...txt") == "file.txt"

    def test_reserved_names(self):
        """Test Windows reserved name handling."""
        assert sanitize_filename("CON.txt").startswith("file_")
        assert sanitize_filename("PRN") == "file_PRN"
        assert sanitize_filename("AUX.log").startswith("file_")
        assert sanitize_filename("COM1.dat").startswith("file_")

    def test_length_limiting(self):
        """Test filename length limiting."""
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name, max_length=255)
        assert len(result) <= 255
        assert result.endswith(".txt")

    def test_empty_and_invalid(self):
        """Test empty and invalid filename handling."""
        assert sanitize_filename("") == "unnamed_file"
        assert sanitize_filename(".") == "unnamed_file"
        assert sanitize_filename("..") == "unnamed_file"
        assert sanitize_filename("   ") == "unnamed_file"


class TestContentDispositionFilename:
    """Test Content-Disposition filename extraction."""

    def test_simple_filename(self):
        """Test simple filename extraction."""
        cd = 'attachment; filename="document.pdf"'
        assert normalize_content_disposition_filename(cd) == "document.pdf"

    def test_filename_without_quotes(self):
        """Test filename without quotes."""
        cd = "attachment; filename=report.xlsx"
        assert normalize_content_disposition_filename(cd) == "report.xlsx"

    def test_filename_star_encoding(self):
        """Test RFC 5987 encoded filename."""
        cd = "attachment; filename*=UTF-8''caf%C3%A9.txt"
        result = normalize_content_disposition_filename(cd)
        assert result is not None
        assert "caf" in result

    def test_no_filename(self):
        """Test Content-Disposition without filename."""
        cd = "attachment"
        assert normalize_content_disposition_filename(cd) is None
        assert normalize_content_disposition_filename(None) is None

    def test_malformed_encoding(self):
        """Test malformed encoded filename handling."""
        cd = "attachment; filename*=INVALID''bad%encoding"
        result = normalize_content_disposition_filename(cd)
        # Should fall back gracefully
        assert result is None or isinstance(result, str)


class TestArchiveExtension:
    """Test archive extension detection."""

    def test_common_archives(self):
        """Test common archive extensions."""
        assert is_archive_extension("file.zip")
        assert is_archive_extension("archive.tar.gz")
        assert is_archive_extension("package.deb")
        assert is_archive_extension("app.dmg")
        assert is_archive_extension("FILE.ZIP")  # Case insensitive

    def test_non_archives(self):
        """Test non-archive files."""
        assert not is_archive_extension("document.pdf")
        assert not is_archive_extension("image.jpg")
        assert not is_archive_extension("script.py")
        assert not is_archive_extension("")

    def test_java_archives(self):
        """Test Java archive formats."""
        assert is_archive_extension("app.jar")
        assert is_archive_extension("webapp.war")
        assert is_archive_extension("enterprise.ear")


class TestFilenameSafety:
    """Test filename safety validation."""

    def test_safe_filename(self):
        """Test safe filename validation."""
        result = validate_filename_safety("document.pdf")
        assert result["safe"] is True
        assert len(result["issues"]) == 0
        assert result["sanitized_filename"] == "document.pdf"

    def test_path_traversal_detection(self):
        """Test path traversal detection."""
        result = validate_filename_safety("../../../etc/passwd")
        assert result["safe"] is False
        assert "Path traversal attempt detected" in result["issues"]

    def test_null_byte_detection(self):
        """Test null byte detection."""
        result = validate_filename_safety("file\x00.txt")
        assert result["safe"] is False
        assert "Null byte in filename" in result["issues"]

    def test_control_character_detection(self):
        """Test control character detection."""
        result = validate_filename_safety("file\x01\x02.txt")
        assert result["safe"] is False
        assert "Control characters in filename" in result["issues"]

    def test_archive_blocking(self):
        """Test archive file blocking."""
        result = validate_filename_safety("archive.zip", allow_archives=False)
        assert result["safe"] is False
        assert "Archive file not allowed" in result["issues"]

        # Should be safe when archives allowed
        result = validate_filename_safety("archive.zip", allow_archives=True)
        assert result["safe"] is True

    def test_long_filename_warning(self):
        """Test long filename warning."""
        long_name = "a" * 300 + ".txt"
        result = validate_filename_safety(long_name)
        assert "Filename too long" in result["issues"]
        assert len(result["sanitized_filename"]) <= 255

    def test_empty_filename(self):
        """Test empty filename handling."""
        result = validate_filename_safety("")
        assert result["safe"] is False
        assert "Empty filename" in result["issues"]


if __name__ == "__main__":
    pytest.main([__file__])
