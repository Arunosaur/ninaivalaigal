#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Response redaction ASGI middleware compatible with legacy imports."""

from __future__ import annotations

import typing as t

from starlette.types import ASGIApp, Message, Receive, Scope, Send

HttpScope = Scope


class ResponseRedactionASGIMiddleware:
    """Stream-friendly response redaction middleware."""

    def __init__(self, app: ASGIApp, detector_fn: t.Callable[[str], str], overlap: int = 64) -> None:
        self.app = app
        self.detector_fn = detector_fn
        self.overlap = max(0, overlap)

    async def __call__(self, scope: HttpScope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        overlap = self.overlap
        detector = self.detector_fn
        tail = ""

        async def redacting_send(message: Message) -> None:
            nonlocal tail

            if message["type"] != "http.response.body":
                await send(message)
                return

            body = message.get("body", b"") or b""
            more = bool(message.get("more_body", False))

            if body:
                text = tail + body.decode("utf-8", errors="replace")
                try:
                    redacted = detector(text)
                except Exception:
                    redacted = text

                if overlap and len(text) >= overlap and more:
                    tail = text[-overlap:]
                    emit_text = redacted[: -len(tail)] if len(redacted) > len(tail) else ""
                else:
                    emit_text = redacted
                    tail = ""

                message = dict(message)
                message["body"] = emit_text.encode("utf-8", errors="replace")

            if not more and tail:
                try:
                    final_chunk = detector(tail).encode("utf-8", errors="replace")
                except Exception:
                    final_chunk = tail.encode("utf-8", errors="replace")
                tail = ""
                interim = dict(message)
                interim["more_body"] = True
                await send(interim)
                await send({"type": "http.response.body", "body": final_chunk, "more_body": False})
                return

            await send(message)

        await self.app(scope, receive, redacting_send)
