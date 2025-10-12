#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
from server.security.multipart.strict_limits import enforce_part_limits, looks_binary


def test_pe_header_is_binary():
    assert looks_binary(b"MZ\x90\x00...."[:10])


def test_pdf_header_is_binary():
    assert looks_binary(b"%PDF-1.7\n..."[:10])


def test_null_byte_is_binary():
    assert looks_binary(b"abc\x00def")


def test_part_limit_enforced():
    try:
        enforce_part_limits(b"x" * 11, max_part_bytes=10)
        raise AssertionError("Expected ValueError to be raised")
    except ValueError:
        pass
