"""
Unicode Normalization Utilities

Provides comprehensive Unicode normalization to prevent evasion attacks
using homoglyphs, zero-width characters, and other Unicode tricks.
"""

import unicodedata

# Zero-width and invisible characters that should be removed
ZERO_WIDTH_CHARS = {
    "\u200B",  # Zero Width Space
    "\u200C",  # Zero Width Non-Joiner
    "\u200D",  # Zero Width Joiner
    "\u2060",  # Word Joiner
    "\uFEFF",  # Zero Width No-Break Space (BOM)
    "\u00AD",  # Soft Hyphen
    "\u034F",  # Combining Grapheme Joiner
    "\u061C",  # Arabic Letter Mark
    "\u180E",  # Mongolian Vowel Separator
}

# Homoglyph mappings to ASCII equivalents
HOMOGLYPH_MAPPINGS = {
    # Cyrillic to Latin
    "А": "A",
    "В": "B",
    "С": "C",
    "Е": "E",
    "Н": "H",
    "І": "I",
    "Ј": "J",
    "К": "K",
    "М": "M",
    "О": "O",
    "Р": "P",
    "Ѕ": "S",
    "Т": "T",
    "Х": "X",
    "У": "Y",
    "а": "a",
    "е": "e",
    "о": "o",
    "р": "p",
    "с": "c",
    "у": "y",
    "х": "x",
    # Greek to Latin
    "Α": "A",
    "Β": "B",
    "Ε": "E",
    "Ζ": "Z",
    "Η": "H",
    "Ι": "I",
    "Κ": "K",
    "Μ": "M",
    "Ν": "N",
    "Ο": "O",
    "Ρ": "P",
    "Τ": "T",
    "Υ": "Y",
    "Χ": "X",
    "α": "a",
    "ο": "o",
    "ρ": "p",
    "υ": "y",
    "χ": "x",
    # Mathematical Bold
    "𝐀": "A",
    "𝐁": "B",
    "𝐂": "C",
    "𝐃": "D",
    "𝐄": "E",
    "𝐅": "F",
    "𝐆": "G",
    "𝐇": "H",
    "𝐈": "I",
    "𝐉": "J",
    "𝐊": "K",
    "𝐋": "L",
    "𝐌": "M",
    "𝐍": "N",
    "𝐎": "O",
    "𝐏": "P",
    "𝐐": "Q",
    "𝐑": "R",
    "𝐒": "S",
    "𝐓": "T",
    "𝐔": "U",
    "𝐕": "V",
    "𝐖": "W",
    "𝐗": "X",
    "𝐘": "Y",
    "𝐙": "Z",
    # Fullwidth characters
    "Ａ": "A",
    "Ｂ": "B",
    "Ｃ": "C",
    "Ｄ": "D",
    "Ｅ": "E",
    "Ｆ": "F",
    "Ｇ": "G",
    "Ｈ": "H",
    "Ｉ": "I",
    "Ｊ": "J",
    "Ｋ": "K",
    "Ｌ": "L",
    "Ｍ": "M",
    "Ｎ": "N",
    "Ｏ": "O",
    "Ｐ": "P",
    "Ｑ": "Q",
    "Ｒ": "R",
    "Ｓ": "S",
    "Ｔ": "T",
    "Ｕ": "U",
    "Ｖ": "V",
    "Ｗ": "W",
    "Ｘ": "X",
    "Ｙ": "Y",
    "Ｚ": "Z",
    "ａ": "a",
    "ｂ": "b",
    "ｃ": "c",
    "ｄ": "d",
    "ｅ": "e",
    "ｆ": "f",
    "ｇ": "g",
    "ｈ": "h",
    "ｉ": "i",
    "ｊ": "j",
    "ｋ": "k",
    "ｌ": "l",
    "ｍ": "m",
    "ｎ": "n",
    "ｏ": "o",
    "ｐ": "p",
    "ｑ": "q",
    "ｒ": "r",
    "ｓ": "s",
    "ｔ": "t",
    "ｕ": "u",
    "ｖ": "v",
    "ｗ": "w",
    "ｘ": "x",
    "ｙ": "y",
    "ｚ": "z",
    "０": "0",
    "１": "1",
    "２": "2",
    "３": "3",
    "４": "4",
    "５": "5",
    "６": "6",
    "７": "7",
    "８": "8",
    "９": "9",
    "．": ".",
}


def remove_zero_width_chars(text: str) -> str:
    """Remove zero-width and invisible characters."""
    if not text:
        return text

    for char in ZERO_WIDTH_CHARS:
        text = text.replace(char, "")

    return text


def normalize_homoglyphs(text: str) -> str:
    """Normalize homoglyphs to ASCII equivalents."""
    if not text:
        return text

    result = []
    for char in text:
        result.append(HOMOGLYPH_MAPPINGS.get(char, char))

    return "".join(result)


def normalize_unicode_for_detection(text: str) -> str:
    """
    Comprehensive Unicode normalization for secret detection.

    Applies NFKC normalization, removes zero-width characters,
    and normalizes homoglyphs to prevent evasion attacks.
    """
    if not text:
        return text

    # Apply NFKC normalization first
    normalized = unicodedata.normalize("NFKC", text)

    # Remove zero-width and invisible characters
    normalized = remove_zero_width_chars(normalized)

    # Normalize homoglyphs to ASCII equivalents
    normalized = normalize_homoglyphs(normalized)

    return normalized


def detect_evasion_attempt(text: str) -> bool:
    """
    Detect if text contains potential Unicode evasion attempts.

    Returns True if suspicious Unicode usage is detected.
    """
    if not text:
        return False

    # Check for zero-width characters
    for char in ZERO_WIDTH_CHARS:
        if char in text:
            return True

    # Check for homoglyphs
    for char in text:
        if char in HOMOGLYPH_MAPPINGS:
            return True

    # Check for mixed scripts (potential homoglyph attack)
    scripts = set()
    for char in text:
        if char.isalpha():
            script = (
                unicodedata.name(char, "").split()[0]
                if unicodedata.name(char, "")
                else "UNKNOWN"
            )
            scripts.add(script)

    # More than 2 different scripts might indicate evasion
    if len(scripts) > 2:
        return True

    return False


# Backward compatibility
def safe_normalize(text: str) -> str:
    """Backward compatibility alias for normalize_unicode_for_detection."""
    return normalize_unicode_for_detection(text)
