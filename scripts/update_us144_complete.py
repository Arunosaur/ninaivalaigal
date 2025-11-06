#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Update US#144 with completion details

import os
import sys

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")


def authenticate():
    auth_url = f"{API_ENDPOINT}/auth"
    auth_data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}
    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            return response.json().get("auth_token")
        return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def get_project_id(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


def update_story(auth_token, story_ref):
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Get story
    url = f"{API_ENDPOINT}/userstories/by_ref?project=1&ref={story_ref}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Could not get story: {response.status_code}")
        return False

    story = response.json()
    story_id = story.get("id")
    version = story.get("version", 1)

    description = """
## Architecture Documentation: Hybrid Compute-Cognitive Architecture - COMPLETE ✅

**US#144 / SPEC-020 Addendum**

### P0: Core Documentation ✅
- ✅ SPEC-020 Addendum created and validated
- ✅ ARCHITECTURE_OVERVIEW.md updated to v3.0 (Hybrid Architecture)
- ✅ Container Language Reference created
- ✅ Architecture validated against SPEC-099 and SPEC-100

### P1: Container Labels ✅ COMPLETE
- ✅ Labeling strategy documented in `CONTAINER_LANGUAGE_REFERENCE.md`
- ✅ Label format: `ninaivalaigal.language` and `ninaivalaigal.layer`
- ✅ Service classification:
  - Compute Layer (Rust/Go): `layer=compute`
  - Cognitive Layer (Python): `layer=cognitive`
  - Routing Layer (Python): `layer=routing`

### P2: Visual Diagrams ✅ COMPLETE
- ✅ Created Mermaid architecture diagram
- ✅ File: `/docs/diagrams/hybrid-architecture.md`
- ✅ Includes service topology, request flow, and layer classification

### Files Created:
- `docs/diagrams/hybrid-architecture.md` - Visual architecture diagrams
- `docs/architecture/US144_COMPLETION_SUMMARY.md` - Completion summary

### Status: ✅ COMPLETE - All P0, P1, and P2 tasks finished
"""

    notes = """
<h2>Architecture Documentation Complete</h2>

<p>✅ <strong>All tasks completed</strong></p>

<h3>Completed Deliverables:</h3>
<ul>
<li>✅ P0: Core documentation (SPEC-020 Addendum, Architecture Overview)</li>
<li>✅ P1: Container labeling strategy documented</li>
<li>✅ P2: Visual architecture diagrams created (Mermaid)</li>
</ul>

<h3>Architecture Diagrams:</h3>
<ul>
<li>✅ Service topology diagram showing all layers</li>
<li>✅ Request flow sequence diagram</li>
<li>✅ Layer classification table</li>
<li>✅ Architecture benefits summary</li>
</ul>

<h3>Files Created:</h3>
<ul>
<li>✅ <code>docs/diagrams/hybrid-architecture.md</code> - Complete visual diagrams</li>
<li>✅ <code>docs/architecture/US144_COMPLETION_SUMMARY.md</code> - Completion summary</li>
</ul>

<h3>Layer Classification:</h3>
<ul>
<li>⚡ <strong>Compute Layer</strong> (Rust/Go): Memory Service (13393), gRPC Gateway (13395)</li>
<li>🧠 <strong>Cognitive Layer</strong> (Python): Graph Service (13394), Business Service (13391), Admin Vendor (13392)</li>
<li>🔀 <strong>Routing Layer</strong> (Python): Core API (13390)</li>
</ul>

<p><strong>Status:</strong> ✅ Complete - All acceptance criteria met</p>
"""

    # Update story
    url = f"{API_ENDPOINT}/userstories/{story_id}"
    payload = {
        "version": version,
        "description": description,
        "description_html": notes,
    }

    try:
        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code in [200, 204]:
            print(f"✅ Successfully updated US#{story_ref}")
            return True
        else:
            print(f"❌ Failed to update story: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error updating story: {e}")
        return False


def main():
    print("=" * 60)
    print("📝 Updating US#144 with Completion Details")
    print("=" * 60)

    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        return 1

    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Project not found")
        return 1

    print("✅ Authenticated and found project")

    if update_story(auth_token, 144):
        print("\n✅ US#144 updated with completion details")
        print("   Story: http://localhost:9000/project/ninaivalaigal/us/144")
        return 0
    else:
        print("\n❌ Failed to update story")
        return 1


if __name__ == "__main__":
    sys.exit(main())
