#!/bin/bash
set -e

NAME=$1
START_SCRIPT=$2

if ! container list | grep -q "$NAME"; then
  echo "[$NAME] not found — recreating..."
  bash "$START_SCRIPT"
else
  echo "[$NAME] restarting..."
  container restart "$NAME"
fi
