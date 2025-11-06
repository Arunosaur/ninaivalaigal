#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Update US#820 with progress on CI markers and Rust integration test setup"""

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

    story = importer.get_user_story("ninaivalaigal", 820)
    if not story:
        print("Story #820 not found")
        return

    print(f"Current story: {story['subject']}")
    print(f"Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print()

    progress_update = f"""

---
**Progress Update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**

## ✅ US#820 - CI Markers and Rust Integration Test Setup

**Developer H**: Working on CI markers and Rust integration test gating

### Completed Work:

1. **✅ Pytest Marker Registration**
   - `rust_integration` marker already registered in `pytest.ini`
   - Marker description complete

2. **✅ Test Gating Logic**
   - `conftest.py` has complete gating logic
   - Tests automatically skipped unless explicitly enabled
   - Three opt-in mechanisms: CLI flag, env vars, feature flag

3. **✅ Test Files Marked**
   - ✅ `tests/integration/test_memory_service_rust.py` - Added marker
   - ✅ `tests/integration/test_memory_service_rust_standalone.py` - Added marker
   - ✅ `services/core-api/tests/test_rust_memory_provider.py` - Already marked

### Gating Mechanism:

Tests are skipped unless one of:
- `PYTEST_RUN_RUST_INTEGRATION=1` environment variable
- `USE_RUST_MEMORY=1` feature flag
- `--run-rust-integration` CLI flag

### Usage:

```bash
# Run Rust integration tests explicitly
pytest --run-rust-integration tests/integration/test_memory_service_rust.py

# Or with environment variable
PYTEST_RUN_RUST_INTEGRATION=1 pytest tests/integration/test_memory_service_rust.py

# Or with feature flag
USE_RUST_MEMORY=1 pytest tests/integration/test_memory_service_rust.py

# Default: Rust tests are skipped
pytest  # rust_integration tests automatically skipped
```

### Next Steps:
- [ ] Verify CI workflows exclude rust_integration by default
- [ ] Add optional CI job for Rust integration tests (nightly or on-demand)
- [ ] Document CI gating strategy in workflow files

**Status**: ✅ Core gating mechanism complete. CI workflow integration pending.
"""

    current_desc = story.get("description", "")
    new_desc = current_desc + progress_update

    updates = {"description": new_desc.strip()}

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
            print("   - Progress update added")
            print("   - CI markers work documented")
        else:
            print("❌ Failed to update story")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
