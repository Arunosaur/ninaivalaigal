#!/usr/bin/env python3
"""
Create Taiga Stories for Missing SPECs

This script:
1. Identifies SPECs without story references
2. Verifies if stories exist in Taiga but aren't cross-referenced
3. Creates stories for truly missing SPECs
4. Updates SPEC READMEs with story references
"""

import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests

# Taiga API Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
PROJECT_SLUG = os.getenv("TAIGA_PROJECT_SLUG", "ninaivalaigal")

# Priority mapping
PRIORITY_MAP = {"HIGH": 2, "MEDIUM": 1, "LOW": 0}

MAX_RETRIES = 3
RETRY_DELAY = 2


def authenticate() -> Optional[str]:
    """Authenticate with Taiga API"""
    try:
        response = requests.post(
            f"{API_ENDPOINT}/auth",
            json={"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json().get("auth_token")
        return None
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None


def get_all_stories(token: str, project_id: int) -> List[Dict]:
    """Get all user stories from Taiga"""
    headers = {"Authorization": f"Bearer {token}"}
    stories = []
    offset = 0
    page_size = 100

    while True:
        try:
            response = requests.get(
                f"{API_ENDPOINT}/userstories",
                headers=headers,
                params={"project": project_id, "offset": offset, "limit": page_size},
                timeout=30,
            )
            if response.status_code != 200:
                break
            data = response.json()
            if not data:
                break
            stories.extend(data)
            if len(data) < page_size:
                break
            offset += page_size
        except Exception as e:
            print(f"⚠️  Error fetching stories: {e}")
            break

    return stories


def extract_spec_from_story(story: Dict) -> Set[int]:
    """Extract SPEC numbers from story"""
    spec_nums = set()
    tags = story.get("tags", [])
    subject = story.get("subject", "")
    description = story.get("description", "")

    # Check tags
    for tag in tags:
        if isinstance(tag, list) and len(tag) > 0:
            tag_str = str(tag[0]).lower()
            matches = re.findall(r"spec[-_]?(\d{3})", tag_str)
            spec_nums.update(int(m) for m in matches)

    # Check subject and description
    for text in [subject, description]:
        matches = re.findall(r"SPEC[-_]?(\d{3})", text, re.IGNORECASE)
        spec_nums.update(int(m) for m in matches)

    return spec_nums


def parse_spec_index() -> List[Dict]:
    """Parse SPEC_INDEX.md"""
    index_path = Path("specs/SPEC_INDEX.md")
    if not index_path.exists():
        return []

    with open(index_path, "r") as f:
        content = f.read()

    specs = []
    pattern = r"^\| (\d{3}) \| ([^|]+) \| ([^|]+) \|"

    for match in re.finditer(pattern, content, re.MULTILINE):
        spec_num = int(match.group(1))
        title = match.group(2).strip()
        status = match.group(3).strip()

        if "Template" in title or "Reserved" in status or "Deprecated" in status:
            continue

        specs.append({"num": spec_num, "title": title, "status": status})

    return specs


def find_spec_readme(spec_num: int) -> Optional[Path]:
    """Find README.md or SPEC.md for a SPEC"""
    specs_dir = Path("specs")
    pattern = f"{spec_num:03d}-*"
    for spec_dir in specs_dir.glob(pattern):
        if spec_dir.is_dir():
            readme = spec_dir / "README.md"
            if readme.exists():
                return readme
            spec_file = spec_dir / "SPEC.md"
            if spec_file.exists():
                return spec_file
    return None


def extract_stories_from_file(file_path: Path) -> Set[int]:
    """Extract US# references from a file"""
    if not file_path.exists():
        return set()
    with open(file_path, "r") as f:
        content = f.read()
    matches = re.findall(r"US#(\d+)", content)
    return {int(m) for m in matches}


def create_story(token: str, project_id: int, ready_status_id: int, story_data: Dict) -> Optional[Dict]:
    """Create a user story in Taiga"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "project": project_id,
        "subject": story_data["subject"],
        "description": story_data["description"],
        "tags": story_data["tags"],
        "status": ready_status_id,
        "points": {str(project_id): story_data.get("points", 0)},
        "priority": story_data.get("priority_id", 1),
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=payload, timeout=30)
            if response.status_code == 201:
                return response.json()
            else:
                print(
                    f"   ❌ Failed (attempt {attempt + 1}/{MAX_RETRIES}): {response.status_code} - {response.text[:200]}"
                )
                time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY)
    return None


def create_spec059_stories(token: str, project_id: int, ready_status_id: int) -> List[Dict]:
    """Create stories for SPEC-059: Unified Macro Intelligence"""
    print("\n📋 Creating SPEC-059: Unified Macro Intelligence stories...")

    stories = [
        {
            "subject": "UMI-001: Macro Schema Definition & Database Design",
            "description": """**SPEC-059 Phase 1: Foundation**

Define and implement database schema for macro storage:
- Macro table schema (id, name, type, trigger_conditions, steps, metadata)
- Macro metadata indexing tables
- Relationships to memory contexts
- Migration scripts

**Acceptance Criteria:**
- ✅ Database schema created and migrated
- ✅ Macro storage tables operational
- ✅ Indexing tables for metadata search
- ✅ Relationships to memory contexts established""",
            "tags": ["spec-059", "macro", "database", "schema", "phase-1"],
            "points": 8,
            "priority_id": PRIORITY_MAP["HIGH"],
        },
        {
            "subject": "UMI-002: Macro Recording API - Option A (Script-based via eM/CLI)",
            "description": """**SPEC-059 Phase 2.1: Script-based Recording**

Implement script-based macro recording via eM CLI:
- CLI commands for macro recording
- Script capture and tokenization
- Macro step extraction
- Related to SPEC-046 (Procedural Macro System)

**Acceptance Criteria:**
- ✅ CLI commands functional
- ✅ Script capture working
- ✅ Tokenization operational
- ✅ Macro steps extracted correctly""",
            "tags": ["spec-059", "macro", "recording", "cli", "phase-2"],
            "points": 8,
            "priority_id": PRIORITY_MAP["HIGH"],
        },
        {
            "subject": "UMI-003: Macro Recording API - Option B (Visual/Replay-based)",
            "description": """**SPEC-059 Phase 2.2: Visual Recording**

Implement visual/replay-based macro recording:
- Screen recording capture
- Action sequence extraction
- Visual step tokenization
- Related to SPEC-047 (Narrative Memory Macros)

**Acceptance Criteria:**
- ✅ Screen recording capture functional
- ✅ Action sequences extracted
- ✅ Visual steps tokenized
- ✅ Replay-ready format generated""",
            "tags": ["spec-059", "macro", "recording", "visual", "phase-2"],
            "points": 8,
            "priority_id": PRIORITY_MAP["MEDIUM"],
        },
        {
            "subject": "UMI-004: Macro Recording API - Option C (Implicit Detection)",
            "description": """**SPEC-059 Phase 2.3: Implicit Detection**

Implement implicit macro detection from repeated behaviors:
- Behavior pattern detection
- Frequency analysis
- Automatic macro suggestion
- User approval workflow

**Acceptance Criteria:**
- ✅ Pattern detection functional
- ✅ Frequency analysis working
- ✅ Auto-suggestions generated
- ✅ User approval workflow operational""",
            "tags": ["spec-059", "macro", "recording", "implicit", "phase-2"],
            "points": 8,
            "priority_id": PRIORITY_MAP["MEDIUM"],
        },
        {
            "subject": "UMI-005: Macro Metadata Indexing System",
            "description": """**SPEC-059 Phase 3: Indexing**

Implement comprehensive macro metadata indexing:
- Trigger condition indexing
- Input context indexing
- Search and retrieval APIs
- Ranking algorithms

**Acceptance Criteria:**
- ✅ Metadata indexing functional
- ✅ Search APIs operational
- ✅ Retrieval working
- ✅ Ranking algorithms implemented""",
            "tags": ["spec-059", "macro", "indexing", "search", "phase-3"],
            "points": 8,
            "priority_id": PRIORITY_MAP["MEDIUM"],
        },
        {
            "subject": "UMI-006: Macro Replay Infrastructure",
            "description": """**SPEC-059 Phase 4: Replay**

Implement macro replay infrastructure:
- Replay execution engine
- Step-by-step execution
- Error handling and rollback
- Re-embedding into AI calls

**Acceptance Criteria:**
- ✅ Replay engine functional
- ✅ Step execution working
- ✅ Error handling operational
- ✅ AI call integration complete""",
            "tags": ["spec-059", "macro", "replay", "execution", "phase-4"],
            "points": 8,
            "priority_id": PRIORITY_MAP["HIGH"],
        },
        {
            "subject": "UMI-007: Macro Dashboard User Interface",
            "description": """**SPEC-059 Phase 5: UI**

Create user interface for macro management:
- Macro list and search
- Macro creation/editing
- Replay controls
- Trigger configuration

**Acceptance Criteria:**
- ✅ Macro dashboard functional
- ✅ List and search working
- ✅ Creation/editing operational
- ✅ Replay controls functional""",
            "tags": ["spec-059", "macro", "ui", "dashboard", "phase-5"],
            "points": 8,
            "priority_id": PRIORITY_MAP["MEDIUM"],
        },
    ]

    created = []
    for story in stories:
        result = create_story(token, project_id, ready_status_id, story)
        if result:
            created.append(result)
            print(f"   ✅ Created: {story['subject']} (US#{result.get('ref', 'N/A')})")
        else:
            print(f"   ❌ Failed: {story['subject']}")

    return created


def create_spec130_stories(token: str, project_id: int, ready_status_id: int) -> List[Dict]:
    """Create stories for SPEC-130: Terminal/CLI Auto Context Capture"""
    print("\n📋 Creating SPEC-130: Terminal/CLI Auto Context Capture stories...")

    stories = [
        {
            "subject": "CLI-CAP-001: Terminal Context Capture Foundation",
            "description": """**SPEC-130 Phase 1: Foundation**

Implement terminal/CLI context capture foundation:
- Shell hook integration (bash/zsh)
- Command history capture
- Environment variable tracking
- Working directory tracking

**Acceptance Criteria:**
- ✅ Shell hooks functional
- ✅ Command history captured
- ✅ Environment variables tracked
- ✅ Working directory tracked""",
            "tags": ["spec-130", "cli", "terminal", "capture", "phase-1"],
            "points": 8,
            "priority_id": PRIORITY_MAP["HIGH"],
        },
        {
            "subject": "CLI-CAP-002: IDE Integration (VS Code & JetBrains)",
            "description": """**SPEC-130 Phase 2: IDE Integration**

Implement IDE integration for context capture:
- VS Code extension
- JetBrains plugin
- Editor state capture
- File context tracking

**Acceptance Criteria:**
- ✅ VS Code extension functional
- ✅ JetBrains plugin working
- ✅ Editor state captured
- ✅ File context tracked""",
            "tags": ["spec-130", "cli", "ide", "integration", "phase-2"],
            "points": 8,
            "priority_id": PRIORITY_MAP["MEDIUM"],
        },
        {
            "subject": "CLI-CAP-003: Context Processing & Storage",
            "description": """**SPEC-130 Phase 3: Processing**

Implement context processing and storage:
- Context tokenization
- Relevance scoring
- Memory storage integration
- Search and retrieval

**Acceptance Criteria:**
- ✅ Context tokenization functional
- ✅ Relevance scoring working
- ✅ Memory storage integrated
- ✅ Search and retrieval operational""",
            "tags": ["spec-130", "cli", "processing", "storage", "phase-3"],
            "points": 8,
            "priority_id": PRIORITY_MAP["MEDIUM"],
        },
    ]

    created = []
    for story in stories:
        result = create_story(token, project_id, ready_status_id, story)
        if result:
            created.append(result)
            print(f"   ✅ Created: {story['subject']} (US#{result.get('ref', 'N/A')})")
        else:
            print(f"   ❌ Failed: {story['subject']}")

    return created


def create_spec131_stories(token: str, project_id: int, ready_status_id: int) -> List[Dict]:
    """Create stories for SPEC-131: Memory Router Rationalization (Phase 2 & 3)"""
    print("\n📋 Creating SPEC-131: Memory Router Rationalization stories (Phase 2 & 3)...")

    # Note: Phase 1 is complete (US#856-857 may exist, but creating Phase 2 & 3)
    stories = [
        {
            "subject": "ROUTER-002: Conditional Router Evaluations",
            "description": """**SPEC-131 Phase 2: Conditional Evaluations**

Evaluate conditional routers for Rust migration:
- health_api.py evaluation (check if in Rust service)
- suggestions_api.py evaluation (only if latency critical)
- metrics evaluation (only if streaming needed)
- Decision documentation

**Acceptance Criteria:**
- ✅ health_api.py evaluated
- ✅ suggestions_api.py evaluated
- ✅ metrics evaluated
- ✅ Decisions documented""",
            "tags": ["spec-131", "router", "evaluation", "conditional", "phase-2"],
            "points": 8,
            "priority_id": PRIORITY_MAP["MEDIUM"],
        },
        {
            "subject": "ROUTER-003: Python Router Cleanup & Deprecation",
            "description": """**SPEC-131 Phase 3: Cleanup**

Clean up deprecated Python routers:
- Remove deprecated router code
- Update service registrations
- Update documentation
- Verify no regressions

**Acceptance Criteria:**
- ✅ Deprecated routers removed
- ✅ Service registrations updated
- ✅ Documentation updated
- ✅ No regressions detected""",
            "tags": ["spec-131", "router", "cleanup", "deprecation", "phase-3"],
            "points": 5,
            "priority_id": PRIORITY_MAP["LOW"],
        },
    ]

    created = []
    for story in stories:
        result = create_story(token, project_id, ready_status_id, story)
        if result:
            created.append(result)
            print(f"   ✅ Created: {story['subject']} (US#{result.get('ref', 'N/A')})")
        else:
            print(f"   ❌ Failed: {story['subject']}")

    return created


def main():
    """Main function"""
    print("=" * 80)
    print("📊 Creating Taiga Stories for Missing SPECs")
    print("=" * 80)

    # Authenticate
    print("\n1️⃣  Authenticating...")
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        sys.exit(1)
    print("   ✅ Authenticated")

    # Get project
    print("\n2️⃣  Getting project...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_ENDPOINT}/projects/by_slug", headers=headers, params={"slug": PROJECT_SLUG}, timeout=10
    )
    if response.status_code != 200:
        print(f"❌ Project lookup failed: {response.status_code}")
        sys.exit(1)
    project = response.json()
    project_id = project.get("id")
    print(f"   ✅ Project ID: {project_id}")

    # Get status IDs
    print("\n3️⃣  Getting status IDs...")
    statuses = {s.get("name"): s.get("id") for s in project.get("us_statuses", [])}
    ready_status_id = statuses.get("Ready", statuses.get("New", list(statuses.values())[0] if statuses else None))
    print(f"   ✅ Ready status ID: {ready_status_id}")

    # Get existing stories
    print("\n4️⃣  Fetching existing stories...")
    all_stories = get_all_stories(token, project_id)
    print(f"   ✅ Found {len(all_stories)} stories")

    # Map stories to SPECs
    stories_by_spec = defaultdict(list)
    for story in all_stories:
        spec_nums = extract_spec_from_story(story)
        for spec_num in spec_nums:
            stories_by_spec[spec_num].append(story)

    # Parse SPEC index
    print("\n5️⃣  Parsing SPEC_INDEX.md...")
    all_specs = parse_spec_index()
    print(f"   ✅ Found {len(all_specs)} SPECs")

    # Identify missing SPECs
    print("\n6️⃣  Identifying missing SPECs...")
    missing_specs = []
    for spec in all_specs:
        spec_num = spec["num"]
        readme_path = find_spec_readme(spec_num)
        file_stories = extract_stories_from_file(readme_path) if readme_path else set()
        taiga_stories = stories_by_spec.get(spec_num, [])

        # Check if truly missing (no file refs AND no Taiga stories)
        if not file_stories and not taiga_stories:
            # Only include Planned/In Progress/Proposed
            if spec["status"] in ["Planned", "In Progress", "Proposed", "Not Implemented"]:
                missing_specs.append(spec)

    print(f"   ✅ Found {len(missing_specs)} SPECs missing stories")

    # Focus on high-priority ones
    priority_specs = [s for s in missing_specs if s["num"] in [59, 130, 131]]

    if not priority_specs:
        print("\n✅ No high-priority SPECs need stories")
        return

    print(f"\n7️⃣  Creating stories for {len(priority_specs)} priority SPECs...")

    all_created = []

    for spec in priority_specs:
        spec_num = spec["num"]
        if spec_num == 59:
            created = create_spec059_stories(token, project_id, ready_status_id)
            all_created.extend(created)
        elif spec_num == 130:
            created = create_spec130_stories(token, project_id, ready_status_id)
            all_created.extend(created)
        elif spec_num == 131:
            created = create_spec131_stories(token, project_id, ready_status_id)
            all_created.extend(created)

    print(f"\n✅ Created {len(all_created)} stories")
    print("\n📋 Created Stories:")
    for story in all_created:
        print(f"   US#{story.get('ref')}: {story.get('subject', 'N/A')[:60]}")


if __name__ == "__main__":
    main()
