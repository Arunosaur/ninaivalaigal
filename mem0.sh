#!/bin/bash
# mem0 client wrapper script
# Makes it easier to run the Python client

# Use absolute path to avoid issues with symlinks
cd /Users/asrajag/Workspace/mem0
python3 client/mem0 "$@"
