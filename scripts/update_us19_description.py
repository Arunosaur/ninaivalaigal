#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Update US#19 story with correct SPEC reference and detailed description"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
from datetime import datetime

from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)

    story = importer.get_user_story("ninaivalaigal", 19)
    if not story:
        print("Story #19 not found")
        return

    print(f"Current story: {story['subject']}")
    print(f"Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print()

    # Correct description - SPEC-061, not SPEC-094
    correct_description = """
# Graph Intelligence Algorithms

**SPEC**: SPEC-061 (Property Graph Intelligence Framework) - NOT SPEC-094

## Objective
Implement and enhance graph traversal and analysis algorithms for intelligent memory graph reasoning.

## Current Implementation Status

**Core Implementation**: `server/graph/graph_reasoner.py` (SPEC-061)

### ✅ Implemented Features:

1. **Context Explanation** (`explain_context()`)
   - Traceable memory retrieval explanations
   - Multi-hop path discovery with reasoning
   - Confidence scoring and supporting evidence

2. **Relevance Inference** (`infer_relevance()`)
   - Proximity-based memory and agent suggestions
   - Multi-hop relationship traversal
   - Scoring and ranking algorithms

3. **Feedback Loop** (`feedback_loop()`)
   - Graph weight updates based on user feedback
   - Traversal parameter adjustment
   - Cache invalidation

4. **Network Analysis** (`analyze_memory_network()`)
   - Network structure analysis
   - Pattern detection and clustering
   - Insights and recommendations generation

### 🔍 Needs Verification/Completion:

- [ ] Comprehensive test coverage for all algorithms
- [ ] API endpoints to expose graph intelligence capabilities
- [ ] Performance benchmarking for traversal algorithms
- [ ] Documentation and usage examples
- [ ] Integration with frontend/UI components

## Next Steps:

1. Review existing implementation in `server/graph/graph_reasoner.py`
2. Verify all helper methods are implemented (`_find_reasoning_paths`, `_calculate_path_relevance`, etc.)
3. Add comprehensive test suite
4. Create API endpoints if missing
5. Document usage and examples

---
**Progress Update {timestamp}**
Developer H assigned. Reviewing implementation status and identifying gaps.
""".format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Update story
    updates = {
        "description": correct_description.strip(),
        "tags": [["spec-061", None], ["graph-intelligence", None], ["algorithms", None], ["intelligence", None]],
    }

    try:
        result = importer.update_user_story(
            story_id=story["id"],
            version=story["version"],
            updates=updates,
            retry_on_version_conflict=True,
            max_retries=3,
        )

        if result:
            print("✅ Story updated successfully")
            print("   - Corrected SPEC reference (SPEC-061, not SPEC-094)")
            print("   - Added detailed implementation status")
            print("   - Updated tags")
        else:
            print("❌ Failed to update story")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
