#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
from typing import Any

from .core import decode, encode


def ToASCII(label: str) -> bytes:
    return encode(label)


def ToUnicode(label: bytes | bytearray) -> str:
    return decode(label)


def nameprep(s: Any) -> None:
    raise NotImplementedError("IDNA 2008 does not utilise nameprep protocol")
