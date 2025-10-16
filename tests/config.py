# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

import os

CORE_API_BASE_URL = os.environ.get("CORE_API_BASE_URL", "http://localhost:8000")
MEMORY_SERVICE_BASE_URL = os.environ.get("MEMORY_SERVICE_BASE_URL", "http://localhost:8001")
GRAPH_AI_SERVICE_BASE_URL = os.environ.get("GRAPH_AI_SERVICE_BASE_URL", "http://localhost:8002")
GATEWAY_BASE_URL = os.environ.get("GATEWAY_BASE_URL", "http://localhost:8080")
