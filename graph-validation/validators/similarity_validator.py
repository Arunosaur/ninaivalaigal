#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
import requests
from metrics.scoring import compute_accuracy


def run(config):
    print("🔍 Validating Similarity Analysis...")
    test_data = open("test_data/memories.json").read()
    response = requests.post(
        f"{config['graph_api']['base_url']}{config['graph_api']['endpoints']['similarity']}",
        json={"memories": test_data},
    )

    results = response.json()
    accuracy = compute_accuracy(results)
    print(f"✅ Similarity Accuracy: {accuracy:.2f}")

    assert accuracy >= config["thresholds"]["similarity_accuracy"], "❌ Similarity accuracy below threshold!"
