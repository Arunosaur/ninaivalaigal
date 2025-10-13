#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
set -euo pipefail
ID="${ID:?Usage: ID=013 NAME='memory-v2' scripts/spec-create.sh}"
NAME="${NAME:?Usage: ID=013 NAME='memory-v2' scripts/spec-create.sh}"

SRC="specs/000-template"
DST="specs/${ID}-${NAME// /-}"

if [ -d "$DST" ]; then
  echo "Spec folder already exists: $DST" >&2; exit 1
fi

mkdir -p "$DST"
rsync -a "$SRC/" "$DST/"
perl -pi -e "s/<ID>/${ID}/g" "$DST"/SPEC.md "$DST"/acceptance.md
echo "Created $DST"
