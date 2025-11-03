#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""End-to-end smoke test for the multipart upload API."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx

API_BASE = os.environ.get("UPLOAD_API_BASE", "http://localhost:13390/upload/multipart")
JWT_TOKEN = os.environ.get("UPLOAD_JWT")
FILE_PATH = Path(os.environ.get("UPLOAD_FILE", "./fixtures/sample.bin"))

HEADERS = {"Authorization": f"Bearer {JWT_TOKEN}"} if JWT_TOKEN else {}


async def _upload_part(upload_url: str, file_path: Path) -> str:
    with file_path.open("rb") as handle:
        response = httpx.put(upload_url, data=handle)
        response.raise_for_status()
    return response.headers.get("etag", "smoke-etag")


async def main() -> None:
    if JWT_TOKEN is None:
        raise SystemExit("UPLOAD_JWT environment variable is required")
    if not FILE_PATH.exists():
        raise SystemExit(f"File not found: {FILE_PATH}")

    async with httpx.AsyncClient(base_url=API_BASE, headers=HEADERS, timeout=30.0) as client:
        start_payload = {
            "object_key": os.environ.get("UPLOAD_OBJECT_KEY", "smoke-tests/sample.bin"),
            "filename": FILE_PATH.name,
            "content_type": os.environ.get("UPLOAD_CONTENT_TYPE", "application/octet-stream"),
            "total_size": FILE_PATH.stat().st_size,
        }
        start_resp = await client.post("/start", json=start_payload)
        start_resp.raise_for_status()
        session = start_resp.json()
        session_id = session["session_id"]
        print("session", session_id)

        url_resp = await client.post(f"/{session_id}/part-url", json={"part_number": 1})
        url_resp.raise_for_status()
        upload_url = url_resp.json()["upload_url"]

        etag = await _upload_part(upload_url, FILE_PATH)

        register_resp = await client.post(
            f"/{session_id}/parts",
            json={"part_number": 1, "etag": etag, "size": FILE_PATH.stat().st_size},
        )
        register_resp.raise_for_status()

        complete_resp = await client.post(f"/{session_id}/complete")
        complete_resp.raise_for_status()
        print("complete", complete_resp.json())


if __name__ == "__main__":
    asyncio.run(main())
