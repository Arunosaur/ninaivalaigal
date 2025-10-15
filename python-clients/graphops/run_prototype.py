# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""Run gRPC client prototype tests."""

import asyncio

from graphops_client.grpc_client_prototype import run_all_tests

if __name__ == "__main__":
    asyncio.run(run_all_tests())
