#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Update Taiga Story #412 with current progress
Developer E - Test Coverage Progress Update
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from taiga_utils import get_story_by_ref, get_taiga_client
except ImportError:
    print("⚠️  taiga_utils not found. Please update story manually in Taiga.")
    sys.exit(1)


def update_story_progress():
    """Update Story #412 with current progress"""

    client = get_taiga_client()
    if not client:
        print("❌ Failed to connect to Taiga")
        return 1

    story = get_story_by_ref(client, 412)
    if not story:
        print("❌ Story #412 not found")
        return 1

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    progress_update = f"""

---

**📊 Progress Update - {timestamp}**

**Current Status:**
- ✅ **load-tester**: 82.8% (EXCEEDED 80% target!) 🎉
- ⚠️ **grpc-gateway**: 79.1% (needs +0.9% to reach 80%)
- ⚠️ **cli-tools**: 44.1% (making good progress, +2.2% this session)

**Work Completed This Session:**

1. **Load-Tester (82.8% ✅ COMPLETE)**
   - Added comprehensive execution tests for metrics, server, and WebSocket commands
   - Added extensive buildOptions tests covering all configuration paths
   - Added tests for init quick command behavior
   - **Status**: Exceeded target, can be marked complete

2. **CLI-Tools (44.1% ⚠️ IN PROGRESS)**
   - Enhanced profile command tests (list, show, use subcommands)
   - Added graph schema, index, and constraints command tests
   - Added tests for display helper functions
   - **Progress**: +2.2% improvement this session
   - **Note**: 80% target may be challenging - interactive commands (0% coverage) are complex to test

3. **gRPC-Gateway (79.1% ⚠️ NEARLY COMPLETE)**
   - Already at 79.1% from previous work
   - Needs only +0.9% to reach 80%
   - **Quick win opportunity** for next session

**Test Files Added:**
- `go-services/load-tester/commands_low_coverage_test.go`
- `go-services/load-tester/grpc_tester_build_options_test.go`
- `go-services/cli-tools/config_profile_execution_comprehensive_test.go`
- `go-services/cli-tools/graph_commands_execution_enhanced_test.go`
- `go-services/cli-tools/graph_index_constraints_execution_test.go`

**Recommendations:**
1. ✅ **Mark load-tester as complete** (82.8% > 80% target)
2. ⚠️ **gRPC-gateway**: Quick win - only needs 2-3 more edge case tests
3. ⚠️ **CLI-tools**: Consider pragmatic approach - 70-75% may be more realistic target
   - Interactive commands (0% coverage) require complex mocking
   - May benefit from split into follow-up story for advanced coverage

**Next Steps:**
- Complete gRPC-gateway quick win (+0.9%)
- Continue CLI-tools core command coverage (target 60%+)
- Consider splitting CLI-tools advanced coverage into separate story

**Status**: ⚠️ **IN PROGRESS** - 1 of 3 services complete, significant progress on all
"""

    # Get current description
    current_desc = story.description or ""

    # Append progress update
    new_desc = current_desc + progress_update

    # Update story
    story.description = new_desc

    # Update status - keep as "In progress" since 2 services still need work
    # Note: If you want to mark load-tester as complete, you could create a subtask

    try:
        story.save()
        print("✅ Story #412 updated successfully!")
        print(f"   - Load-tester: 82.8% (EXCEEDED target)")
        print(f"   - gRPC-gateway: 79.1% (needs +0.9%)")
        print(f"   - CLI-tools: 44.1% (in progress)")
        return 0
    except Exception as e:
        print(f"❌ Failed to update story: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(update_story_progress())
