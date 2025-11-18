#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Router package for modularized FastAPI endpoints.

This package contains all FastAPI router modules for the ninaivalaigal platform.
Routers are organized by domain (contexts, memory, organizations, etc.)
and can be imported individually or as a package.
"""

# Export commonly used routers for convenience
# Individual routers should be imported directly when needed:
# from server.routers import contexts, memory, organizations
