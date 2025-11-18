#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga user stories for SPEC-059: Unified Macro Intelligence.

Usage:
    python3 scripts/create_spec059_stories.py
"""

import os
import sys

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

PROJECT_SLUG = "ninaivalaigal"
SPEC_NUMBER = "059"
SPEC_TITLE = "Unified Macro Intelligence"


def authenticate():
    """Authenticate and get auth token."""
    print("\n1️⃣  Authenticating...")
    response = requests.post(
        f"{API_ENDPOINT}/auth",
        json={"type": "normal", "username": USERNAME, "password": PASSWORD},
    )
    if response.status_code == 200:
        auth_token = response.json()["auth_token"]
        print("✅ Authenticated")
        return {"Authorization": f"Bearer {auth_token}"}
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        sys.exit(1)


def get_project_id(headers, project_slug):
    """Get project ID by slug."""
    response = requests.get(
        f"{API_ENDPOINT}/projects/by_slug",
        headers=headers,
        params={"slug": project_slug},
    )
    if response.status_code == 200:
        return response.json().get("id")
    else:
        print(f"❌ Failed to get project {project_slug}: {response.status_code}")
        sys.exit(1)


def get_status_id(headers, project_id, status_name):
    """Get status ID by name."""
    response = requests.get(
        f"{API_ENDPOINT}/userstory-statuses",
        headers=headers,
        params={"project": project_id},
    )
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name") == status_name:
                return status.get("id")
    return None


def create_story(headers, project_id, subject, description, status_id=None):
    """Create a user story."""
    payload = {
        "project": project_id,
        "subject": subject,
        "description": description,
        "tags": [f"SPEC-{SPEC_NUMBER}"],
    }

    if status_id:
        payload["status"] = status_id

    response = requests.post(
        f"{API_ENDPOINT}/userstories",
        headers={**headers, "Content-Type": "application/json"},
        json=payload,
    )

    if response.status_code == 201:
        return response.json()
    else:
        print(f"❌ Failed to create story: {response.status_code} - {response.text[:200]}")
        return None


def main():
    """Main function."""
    print("=" * 80)
    print(f"📋 Creating Taiga Stories for SPEC-{SPEC_NUMBER}")
    print(f"   Project: {PROJECT_SLUG}")
    print(f"   SPEC: {SPEC_TITLE}")
    print("=" * 80)

    # Authenticate
    headers = authenticate()

    # Get project ID
    print("\n2️⃣  Getting project...")
    project_id = get_project_id(headers, PROJECT_SLUG)
    print(f"✅ Project ID: {project_id}")

    # Get status IDs
    print("\n3️⃣  Getting status IDs...")
    new_status_id = get_status_id(headers, project_id, "New")
    done_status_id = get_status_id(headers, project_id, "Done")
    print(f"✅ New status ID: {new_status_id}")
    print(f"✅ Done status ID: {done_status_id}")

    # Define stories based on SPEC-059 deliverables
    stories = [
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Macro Intelligence Engine - Complete",
            "description": """**Objective**: Implement macro intelligence analysis engine.

**Status**: ✅ **COMPLETE**

**Completed Work**:
- `unified_macro_intelligence_api.py` implemented in multiple services:
  - `services/core-api/lib/unified_macro_intelligence_api.py`
  - `services/graph-service/lib/unified_macro_intelligence_api.py`
  - `services/business-service/lib/unified_macro_intelligence_api.py`
  - `server/unified_macro_intelligence_api.py`
- MacroIntelligenceEngine class with:
  - Pattern recognition
  - Trend analysis
  - Insight generation
  - Prediction capabilities
- API endpoints:
  - `POST /macro-intelligence/analyze` - Generate intelligence analysis
  - `GET /macro-intelligence/insights/{analysis_id}` - Retrieve results
- Integration with RelevanceEngine and Redis
- Pydantic models for requests/responses

**Key Features**:
- Memory pattern analysis
- Trend detection
- Predictive insights
- Recommendation generation
- Confidence scoring

**Deliverables**:
- ✅ Macro intelligence engine
- ✅ Intelligence API endpoints
- ✅ Pattern recognition
- ✅ Trend analysis""",
            "status": "Done",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Macro Schema Definition & Database Design",
            "description": """**Objective**: Define and implement database schema for macro storage.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Design macro schema:
  - Macro definition table
  - Macro execution history
  - Macro metadata (triggers, context)
  - Version tracking
- [ ] Create Alembic migrations
  - Macro table with proper indexes
  - Foreign key relationships
  - Support for all three capture modes
- [ ] Implement macro storage models:
  - Pydantic models for macro definitions
  - SQLAlchemy ORM models
  - Relationship with memory_records

**Acceptance Criteria**:
- [ ] Database schema supports all macro types
- [ ] Proper indexes for performance
- [ ] Foreign key relationships defined
- [ ] Alembic migrations created and tested
- [ ] Schema supports versioning

**Deliverables**:
- Macro schema definition
- Database migrations
- ORM models
- Schema documentation

**Priority**: High - Foundation for macro recording and replay""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Macro Recording API - Option A (Script-based via eM/CLI)",
            "description": """**Objective**: Implement script-based macro recording via eM CLI.

**Status**: ❌ **NOT IMPLEMENTED**

**Scope**: Option A - Script-based capture mode
**Related**: SPEC-046 (Procedural Macro System)

**Tasks**:
- [ ] Design CLI commands:
  - `e^M macro start` - Begin macro recording
  - `e^M macro stop` - End macro recording
  - `e^M macro list` - List recorded macros
- [ ] Implement macro recording API:
  - Capture script/command sequences
  - Serialize procedural steps
  - Link to memory contexts
- [ ] Macro metadata capture:
  - Trigger conditions
  - Input context
  - Execution parameters
- [ ] Integration with macro schema
- [ ] Redis-backed caching for active recordings

**Acceptance Criteria**:
- [ ] CLI commands functional
- [ ] Script sequences captured
- [ ] Macros linked to memory contexts
- [ ] Metadata properly stored
- [ ] Integration with SPEC-046 procedural macros

**Deliverables**:
- CLI commands for macro recording
- Recording API endpoints
- Serialization format
- Context linkage

**Priority**: High - Core capture mode""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Macro Recording API - Option B (Visual/Replay-based)",
            "description": """**Objective**: Implement visual/replay-based macro recording (screen-recorded demonstrations).

**Status**: ❌ **NOT IMPLEMENTED**

**Scope**: Option B - Visual/Replay-based capture mode
**Related**: SPEC-047 (Narrative Memory Macros)

**Tasks**:
- [ ] Design visual recording API:
  - Screen capture integration
  - Audio recording support
  - Timeline generation
- [ ] Implement recording infrastructure:
  - Integration with OBS, browser API, or ffmpeg
  - Video storage in object store
  - Transcription generation
- [ ] Macro metadata capture:
  - Screen interactions
  - Audio transcriptions
  - Timeline markers
- [ ] Integration with macro schema
- [ ] Link to narrative memories

**Acceptance Criteria**:
- [ ] Screen recording functional
- [ ] Audio recording supported
- [ ] Timeline generated
- [ ] Transcription created
- [ ] Integration with SPEC-047 narrative macros

**Deliverables**:
- Visual recording API
- Video/audio storage
- Timeline generation
- Transcription service

**Priority**: High - Core capture mode""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Macro Recording API - Option C (Implicit Detection)",
            "description": """**Objective**: Implement implicit macro detection from repeated user behaviors.

**Status**: ❌ **NOT IMPLEMENTED**

**Scope**: Option C - Implicit (passively detected) capture mode

**Tasks**:
- [ ] Design behavior analysis:
  - Pattern detection algorithms
  - Frequency analysis
  - Context similarity matching
- [ ] Implement passive detection:
  - Monitor user actions
  - Identify repeated patterns
  - Generate macro candidates
- [ ] User confirmation flow:
  - Suggest macro candidates
  - User approval/rejection
  - Macro refinement
- [ ] Integration with intelligence engine:
  - Use existing pattern analysis
  - Leverage MacroIntelligenceEngine
- [ ] Privacy and consent:
  - User opt-in/opt-out
  - Data privacy compliance

**Acceptance Criteria**:
- [ ] Behavior patterns detected
- [ ] Macro candidates generated
- [ ] User confirmation flow works
- [ ] Privacy controls implemented
- [ ] Integration with intelligence engine

**Deliverables**:
- Behavior analysis algorithms
- Pattern detection system
- User confirmation UI/API
- Privacy controls

**Priority**: Medium - Advanced feature""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Macro Metadata Indexing System",
            "description": """**Objective**: Implement comprehensive macro metadata indexing for search and retrieval.

**Status**: 🟡 **PARTIALLY COMPLETE** (Intelligence engine exists, indexing pending)

**Tasks**:
- [ ] Design indexing schema:
  - Trigger condition indexing
  - Input context indexing
  - Tag and category indexing
  - Search vector embeddings
- [ ] Implement indexing infrastructure:
  - Integration with Redis for fast lookup
  - PostgreSQL indexes for queries
  - Vector search for semantic matching
- [ ] Metadata extraction:
  - Extract from macro definitions
  - Parse trigger conditions
  - Index context information
- [ ] Search and retrieval:
  - Keyword search
  - Semantic search
  - Context-based retrieval
  - Ranking algorithms

**Acceptance Criteria**:
- [ ] All macro metadata indexed
- [ ] Fast search performance
- [ ] Semantic search functional
- [ ] Context-based retrieval works
- [ ] Ranking produces relevant results

**Deliverables**:
- Indexing schema
- Indexing infrastructure
- Search API endpoints
- Ranking system

**Priority**: High - Enables macro discovery""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Macro Replay Infrastructure",
            "description": """**Objective**: Implement macro replay infrastructure for executing recorded macros.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Design replay engine:
  - Macro execution framework
  - Step-by-step replay
  - Error handling and recovery
  - Context restoration
- [ ] Implement replay infrastructure:
  - Script-based replay (Option A)
  - Visual replay (Option B)
  - Context-aware replay
  - Replay history tracking
- [ ] Security and sandboxing:
  - Isolated execution environment
  - Permission checks
  - Audit logging
- [ ] Re-embedding into AI calls:
  - Integration with AI prompts
  - Context injection
  - Parameter substitution
- [ ] Testing and validation:
  - Replay accuracy tests
  - Error scenario handling
  - Performance testing

**Acceptance Criteria**:
- [ ] All three macro types can be replayed
- [ ] Security sandboxing functional
- [ ] Error handling robust
- [ ] AI integration works
- [ ] Audit trail maintained

**Deliverables**:
- Replay engine
- Execution framework
- Security sandbox
- AI integration
- Test suite

**Priority**: High - Core functionality""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Macro Dashboard User Interface",
            "description": """**Objective**: Create user interface for macro management and interaction.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Design dashboard UI:
  - Macro list view
  - Macro detail view
  - Recording interface
  - Replay controls
- [ ] Implement dashboard components:
  - Macro browser
  - Recording controls
  - Replay interface
  - Macro editor
- [ ] Features:
  - Search and filter macros
  - Tag management
  - Trigger configuration
  - Execution history
- [ ] Integration:
  - Connect to macro APIs
  - Real-time updates
  - Error handling UI
- [ ] User experience:
  - Intuitive navigation
  - Clear feedback
  - Help documentation

**Acceptance Criteria**:
- [ ] All macro operations accessible via UI
- [ ] Recording works from UI
- [ ] Replay functional
- [ ] Search and filter work
- [ ] User-friendly interface

**Deliverables**:
- Macro dashboard UI
- Recording interface
- Replay controls
- Management interface

**Priority**: Medium - User-facing feature""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Multi-Agent Expert System Implementation",
            "description": """**Objective**: Implement multi-agent expert roles from SPEC-ENHANCED.md.

**Status**: ❌ **NOT IMPLEMENTED** (Specification complete in SPEC-ENHANCED.md)

**Scope**: Enhanced feature with Planning Expert, Memory Expert, Tool Orchestration Expert

**Tasks**:
- [ ] Implement Planning Expert:
  - Strategic task decomposition
  - Resource allocation
  - Timeline estimation
  - Risk assessment
- [ ] Implement Memory Expert:
  - Context retrieval and storage
  - Pattern recognition
  - Historical analysis
  - Knowledge base curation
- [ ] Implement Tool Orchestration Expert:
  - Tool selection and routing
  - API integration management
  - Execution coordination
  - Result aggregation
- [ ] Expert collaboration system:
  - Role-switching protocols
  - Goal passing mechanisms
  - Shared context management
- [ ] Integration with macro system:
  - Expert-guided macro creation
  - Intelligent macro suggestions
  - Expert-assisted replay

**Acceptance Criteria**:
- [ ] All three expert roles implemented
- [ ] Collaboration protocols functional
- [ ] Shared context management works
- [ ] Integration with macro system
- [ ] Expert suggestions improve macro quality

**Deliverables**:
- Planning Expert implementation
- Memory Expert implementation
- Tool Orchestration Expert implementation
- Collaboration framework
- Integration with macro system

**Priority**: Medium - Advanced feature""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Macro Intelligence Integration",
            "description": """**Objective**: Integrate completed intelligence engine with macro recording and replay.

**Status**: 🟡 **PARTIAL** (Engine exists, integration pending)

**Tasks**:
- [ ] Connect intelligence to recording:
  - Suggest macro creation from patterns
  - Intelligent metadata extraction
  - Context-aware tagging
- [ ] Integrate intelligence with replay:
  - Smart macro recommendations
  - Context-based macro selection
  - Predictive replay triggers
- [ ] Enhanced analytics:
  - Macro usage analytics
  - Effectiveness metrics
  - Optimization suggestions
- [ ] User feedback loop:
  - Collect replay outcomes
  - Improve intelligence models
  - Personalize recommendations

**Acceptance Criteria**:
- [ ] Intelligence informs macro creation
- [ ] Smart recommendations work
- [ ] Analytics provide insights
- [ ] Feedback loop functional
- [ ] User experience improved

**Deliverables**:
- Recording intelligence integration
- Replay intelligence integration
- Analytics dashboard
- Feedback mechanism

**Priority**: Medium - Enhances existing intelligence""",
            "status": "New",
        },
    ]

    # Create stories
    print("\n4️⃣  Creating stories...")
    created_stories = []
    failed_stories = []

    for idx, story_data in enumerate(stories, 1):
        print(f"\n   Creating story {idx}/{len(stories)}: {story_data['subject'][:60]}...")

        status_id = done_status_id if story_data["status"] == "Done" else new_status_id

        created = create_story(
            headers,
            project_id,
            story_data["subject"],
            story_data["description"],
            status_id=status_id,
        )

        if created:
            ref = created.get("ref")
            created_stories.append((ref, story_data["subject"]))
            print(f"   ✅ Created US#{ref}")
        else:
            failed_stories.append(story_data["subject"])
            print(f"   ❌ Failed to create story")

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    print("=" * 80)
    print(f"✅ Successfully created: {len(created_stories)}")
    if failed_stories:
        print(f"❌ Failed to create: {len(failed_stories)}")

    if created_stories:
        print("\nCreated stories:")
        for ref, subject in created_stories:
            print(f"  US#{ref}: {subject[:65]}")

    print("=" * 80)


if __name__ == "__main__":
    main()




