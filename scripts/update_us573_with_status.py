#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update US#573 (SPEC-095) story with accurate status"""

import os
import sys

import requests

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Update US#573 story with accurate status"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    story_ref = 573
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"❌ Story US#{story_ref} not found in Taiga")
        return

    print(f"✅ Found story: SPEC-095: Memory Graph State Reconciliation")
    print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print(f"   Current version: {story.get('version')}")

    description = """**SPEC-095: Memory Graph State Reconciliation**

**Status:** 🔄 NEW (Implementation: 0% complete)
**Phase:** Phase 3
**Priority:** Medium
**Dependencies:** SPEC-060 (Property Graph Memory Model), SPEC-061 (Graph Intelligence Framework)

---

## 📋 Objective

Implement **bidirectional state reconciliation** between memory store (relational) and graph store (Apache AGE) to ensure consistency, detect discrepancies, and resolve conflicts.

**Distinction from Related SPECs:**
- **SPEC-060:** Graph schema/model definition (foundation)
- **SPEC-061:** Graph intelligence and reasoning (different concern)
- **SPEC-127:** Memory federation (cross-team/org sync, different scope)
- **SPEC-095:** State reconciliation (consistency between memory and graph)

---

## ✅ What Exists (In Related SPECs)

### SPEC-060: Property Graph Memory Model (Complete)
- ✅ Graph schema defined (nodes, edges)
- ✅ Apache AGE integration
- ✅ Graph model established

### SPEC-061: Graph Intelligence Framework (Complete)
- ✅ Graph reasoning layer
- ✅ Context explanation, relevance inference
- ✅ Graph intelligence operations

### Graph Sync (One-Way) - Not SPEC-095
- ✅ `server/graph_intelligence_integration_api.py` - One-way sync (relational → graph)
- ✅ Batch synchronization from relational DB to graph nodes
- ✅ Redis caching for sync operations
- ❌ **Different Scope:** One-way sync, not reconciliation

---

## ❌ What's Missing (SPEC-095)

### 1. Bidirectional Synchronization ❌
- Current: Only relational → graph (one-way)
- Needed: Graph → relational sync capability
- Needed: Conflict resolution when both sides change

### 2. Consistency Checking ❌
- Algorithm to detect discrepancies between memory and graph
- Validation queries to compare states
- Drift detection (when states diverge over time)

### 3. Reconciliation Engine ❌
- Algorithm to resolve conflicts
- Priority rules (which source of truth wins?)
- Merge strategies for conflicts

### 4. Audit & Monitoring ❌
- Track reconciliation operations
- Monitor consistency metrics
- Alert on reconciliation failures

### 5. API Endpoints ❌
- `POST /graph/reconcile` - Trigger reconciliation
- `GET /graph/consistency` - Check consistency status
- `GET /graph/reconcile/history` - Reconciliation history

---

## 🎯 Proposed Implementation

### Phase 1: Consistency Checking
1. Implement algorithms to compare memory and graph states
2. Detect discrepancies (missing nodes, mismatched properties, orphaned edges)
3. Generate discrepancy reports

### Phase 2: Reconciliation Engine
1. Implement conflict resolution algorithms
2. Define priority rules (memory-first vs graph-first vs merge)
3. Implement merge strategies

### Phase 3: Bidirectional Sync
1. Extend current one-way sync to bidirectional
2. Handle conflicts during sync
3. Implement reconciliation workflows

### Phase 4: API Endpoints
1. `POST /graph/reconcile` - Trigger reconciliation
2. `GET /graph/consistency` - Check consistency status
3. `GET /graph/reconcile/history` - Reconciliation history

### Phase 5: Audit & Monitoring
1. Track reconciliation operations
2. Monitor consistency metrics
3. Integrate with alerting system

---

## 🔗 Dependencies

### Required
- **SPEC-060:** Property Graph Memory Model (Complete) - Provides graph schema
- **SPEC-061:** Graph Intelligence Framework (Complete) - Provides graph operations

### Coordination Needed
- **SPEC-127:** Context Bridge & Memory Federation (Complete) - May need coordination for cross-system consistency

---

## 📊 Related Documentation

- **Analysis Document:** `docs/spec-analysis/SPEC_095_COMPREHENSIVE_ANALYSIS.md`
- **SPEC-060:** `specs/060-property-graph-memory-model/README.md` - Property Graph Memory Model
- **SPEC-061:** `specs/061-graph-reasoner/README.md` - Graph Intelligence Framework
- **SPEC-127:** `specs/127-context-bridge-system/README.md` - Context Bridge & Memory Federation
- **SPEC_INDEX.md:** Line 163 - SPEC-095 entry

---

**Status:** 🔄 NEW (0% implementation, placeholder needs definition)
**Last Updated:** January 2025"""

    # Get status ID for "New"
    api_endpoint = f"{taiga_url}/api/v1"
    headers = {"Authorization": f"Bearer {importer._auth_token}", "Content-Type": "application/json"}

    project_info = requests.get(f"{api_endpoint}/projects/by_slug?slug=ninaivalaigal", headers=headers).json()
    project_id = project_info["id"]

    statuses = requests.get(f"{api_endpoint}/userstory-statuses?project={project_id}", headers=headers).json()
    new_status_id = None
    for status in statuses:
        if status.get("name", "").lower() == "new":
            new_status_id = status["id"]
            break

    update_payload = {"description": description, "version": story.get("version", 1)}

    if new_status_id and story.get("status_extra_info", {}).get("name", "").lower() != "new":
        update_payload["status"] = new_status_id

    response = requests.patch(f"{api_endpoint}/userstories/{story['id']}", headers=headers, json=update_payload)

    if response.status_code == 200:
        print("✅ Story description and status updated")
        if new_status_id:
            print(f"   Status changed to 'New'")
    else:
        print(f"❌ Failed to update story: {response.status_code}")
        print(f"   Response: {response.text[:200]}")


if __name__ == "__main__":
    main()
