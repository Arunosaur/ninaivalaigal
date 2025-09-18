#!/usr/bin/env bash
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
