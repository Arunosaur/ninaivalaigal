#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Create Taiga story for SPEC-144: Context-Aware Feedback System"""

import os
import sys

import requests

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Create US story for SPEC-144"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    api_endpoint = f"{taiga_url}/api/v1"
    headers = {"Authorization": f"Bearer {importer._auth_token}", "Content-Type": "application/json"}

    project_info = requests.get(f"{api_endpoint}/projects/by_slug?slug=ninaivalaigal", headers=headers).json()
    project_id = project_info["id"]

    # Get status ID for "New" or "Planned"
    statuses = requests.get(f"{api_endpoint}/userstory-statuses?project={project_id}", headers=headers).json()
    new_status_id = None
    for status in statuses:
        if status.get("name", "").lower() in ["new", "planned"]:
            new_status_id = status["id"]
            break

    # Read SPEC-144 README for description
    spec_readme_path = "specs/144-context-aware-feedback-system/README.md"
    spec_description = ""
    if os.path.exists(spec_readme_path):
        with open(spec_readme_path, "r") as f:
            spec_description = f.read()

    description = f"""**SPEC-144: Context-Aware Feedback System**

**Status:** 📋 **PLANNED**
**Phase:** Phase 3
**Priority:** High
**Category:** Intelligence / AI Feedback

---

## 🎯 Overview

**Context-Aware Feedback System** is a meta-feedback layer that sits above memory-centric feedback (SPEC-040), focused on **AI reasoning context itself** rather than individual memory relevance. This system learns not just which memories are good, but how **context composition** affects the AI's downstream quality.

**Distinction from SPEC-040:**
- **SPEC-040:** Memory-centric feedback (users score individual memories, adjust memory relevance) ✅ Complete
- **SPEC-144:** Context-aware feedback (feedback on context composition, reasoning quality, prompt optimization) 📋 Planned

---

## 🧠 Core Purpose

**Ninaivalaigal is evolving into a context intelligence engine, not just a memory repository.** Context-aware feedback enables the system to learn:
- Which context windows work best for different query types
- How to prioritize graph nodes for reasoning
- How to auto-tune prompt windows based on feedback
- How to balance context length, relevance, and tone

Without context-aware feedback:
- GraphOps layer can't learn which nodes to prioritize for reasoning
- Reasoner can't auto-tune its prompt window
- The e^M Feedback Loop stays static — it improves recall, but not reasoning context

---

## 📋 Key Features

### 1. Context Quality Feedback Collection
- Context length feedback ("Response feels off-topic" → Reduce window)
- Context relevance feedback ("You ignored my last summary" → Boost recall)
- Tone/alignment feedback ("Too technical" → Adjust weighting)
- Retrieval bias feedback ("Keeps surfacing one user's memories" → Apply fairness)

### 2. Context Composition Scorer
- Analyzes context composition quality before sending to LLM
- Scores based on memory diversity, temporal distribution, relevance, tone, length

### 3. Context Compression Model
- Intelligently compresses context when too long
- Prioritizes memories based on feedback patterns and query type

### 4. LLM Telemetry Correlation
- Correlates feedback with LLM output quality
- Tracks response relevance, user satisfaction, error rates

### 5. Adaptive Context Gating
- Dynamic context window sizing based on task type
- Query classification and context weighting adjustment

---

## 🔗 Dependencies

### Required (Complete)
- **SPEC-040:** Feedback Loop System (provides memory feedback ground truth) ✅
- **SPEC-031:** Memory Relevance Ranking (context relevance calculation) ✅
- **SPEC-033:** Redis Integration (event storage and processing) ✅
- **SPEC-061:** Graph Intelligence (graph node prioritization) ✅

### Related (Planned)
- **SPEC-063:** Agentic Core Execution (context injection points)
- **SPEC-135:** Multi-Agent Expert Protocol (agent context coordination)

---

## 📊 Implementation Phases

### Phase 1: Foundation (Weeks 1-4)
- [ ] Context feedback collection API
- [ ] Basic context composition scoring
- [ ] Database schema for context feedback
- [ ] Integration with SPEC-040 feedback data

### Phase 2: Analysis (Weeks 5-8)
- [ ] LLM telemetry correlation
- [ ] Context compression model (basic)
- [ ] Context quality dashboard
- [ ] Feedback pattern analysis

### Phase 3: Optimization (Weeks 9-12)
- [ ] Adaptive context gating
- [ ] Advanced context compression
- [ ] Query type classification
- [ ] Context composition recommendations

### Phase 4: Integration (Weeks 13-16)
- [ ] GraphOps integration (node prioritization)
- [ ] Reasoner integration (prompt window tuning)
- [ ] Full e^M feedback loop integration
- [ ] Performance optimization

---

## 💡 Benefits

**Immediate:**
- Better context composition before LLM calls
- Reduced token usage while maintaining quality
- Improved response relevance

**Long-term:**
- Self-improving context intelligence layer
- GraphOps learns optimal node prioritization
- Reasoner auto-tunes prompt windows
- e^M feedback loop becomes truly dynamic

---

## 🔗 Related SPECs

- **SPEC-040:** Feedback Loop System (Memory Accuracy + Relevance Signals) - ✅ Complete
- **SPEC-097:** Feedback Loop for AI Context - ⚠️ Unclear scope (may be duplicate of SPEC-040)

---

## 📚 Documentation

**SPEC Location:** `specs/144-context-aware-feedback-system/README.md`

**Full Specification:** See SPEC README for complete details including architecture, API endpoints, database schema, and implementation roadmap.

---

**Status:** 📋 PLANNED - Context-aware feedback for reasoning & prompt optimization
**Next Step:** Define detailed architecture and acceptance criteria
**ETA:** Phase 3 (after SPEC-040 stabilization)

---

*This SPEC represents the natural Phase 3+ evolution beyond SPEC-040's memory-centric feedback, enabling Ninaivalaigal to become a true context intelligence engine.*"""

    story_data = {
        "subject": "SPEC-144: Context-Aware Feedback System",
        "description": description,
        "project": project_id,
        "tags": ["spec-144", "context-feedback", "ai-feedback", "phase-3", "intelligence"],
    }

    if new_status_id:
        story_data["status"] = new_status_id

    response = requests.post(f"{api_endpoint}/userstories", headers=headers, json=story_data)

    if response.status_code == 201:
        story = response.json()
        print(f"✅ Created story: US#{story.get('ref')}: {story.get('subject')}")
        print(f"   Status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
        print(f"   ID: {story.get('id')}")

        # Save story details
        output_file = "docs/spec-analysis/US644_STORY_DETAILS.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        import json

        with open(output_file, "w") as f:
            json.dump(story, f, indent=2, default=str)
        print(f"   Story details saved to: {output_file}")
    else:
        print(f"❌ Failed to create story: {response.status_code}")
        print(f"   Response: {response.text[:500]}")


if __name__ == "__main__":
    main()
