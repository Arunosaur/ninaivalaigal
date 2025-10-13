#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/rawtest")
async def raw_test(request: Request):
    body = await request.body()
    return {"length": len(body)}
