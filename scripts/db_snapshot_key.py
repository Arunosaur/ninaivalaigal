#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
import glob
import hashlib


def hash_migrations():
    paths = sorted(glob.glob("alembic/versions/*.py") + glob.glob("server/memory/db/migrations/*.sql"))
    h = hashlib.sha256()
    if not paths:
        return "no-migrations"
    for p in paths:
        with open(p, "rb") as f:
            h.update(p.encode("utf-8"))
            h.update(f.read())
    return h.hexdigest()


if __name__ == "__main__":
    print(hash_migrations())
