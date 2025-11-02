#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""
Create Taiga user stories for SPEC-067: Advanced D3.js Visualizations.

Usage:
    python3 scripts/create_spec067_stories.py
"""

import os
import sys

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

PROJECT_SLUG = "ninaivalaigal"
SPEC_NUMBER = "067"
SPEC_TITLE = "Advanced D3.js Visualizations"
DEVELOPER_C_USERNAME = "developer-c"


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


def get_user_id(headers, username):
    """Get user ID by username."""
    response = requests.get(f"{API_ENDPOINT}/users/me", headers=headers)
    if response.status_code == 200:
        me = response.json()
        if me.get("username") == username:
            return me.get("id")

    # Try to get all users
    project_id = get_project_id(headers, PROJECT_SLUG)
    response = requests.get(f"{API_ENDPOINT}/users", headers=headers, params={"project": project_id})
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("username") == username:
                return user.get("id")

    return None


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


def create_story(headers, project_id, subject, description, assignee_id, status_id=None):
    """Create a user story."""
    payload = {
        "project": project_id,
        "subject": subject,
        "description": description,
        "tags": [f"SPEC-{SPEC_NUMBER}"],
    }

    if assignee_id:
        payload["assigned_to"] = assignee_id

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
        print(f"❌ Failed to create story: {response.status_code} - " f"{response.text[:200]}")
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

    # Get user ID for Developer C
    print(f"\n3️⃣  Getting user ID for {DEVELOPER_C_USERNAME}...")
    assignee_id = get_user_id(headers, DEVELOPER_C_USERNAME)
    if assignee_id:
        print(f"✅ Developer C ID: {assignee_id}")
    else:
        print("⚠️  Developer C not found, stories will be unassigned")
        assignee_id = None

    # Get status IDs
    print("\n4️⃣  Getting status IDs...")
    new_status_id = get_status_id(headers, project_id, "New")
    print(f"✅ New status ID: {new_status_id}")

    # Define stories based on SPEC-067 remaining deliverables
    stories = [
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Current D3.js Foundation - Complete",
            "description": """**Objective**: Document completion of basic D3.js visualization foundation.

**Status**: ✅ **COMPLETE**

**Completed Work**:
- ✅ RankedMemoryVisualization: Basic D3.js visualization for PageRank-ranked memories
  - Location: `config/frontend/frontend-ai-intelligence.js`
  - Features: PageRank-based ranked memory visualization with D3.js
- ✅ TimelineVisualization: D3 timeline visualization
  - Location: `config/frontend/frontend-timeline-visualization.js`
  - Features: Timeline visualization with D3.js
- ✅ Basic Data APIs: Partial visualization data in insights_api
  - Knowledge hotspots data with visualization_data
  - Timeline visualization data in timeline_api
- ✅ D3.js Integration: Basic D3.js setup and integration

**Key Features**:
- Basic D3.js visualizations
- Ranked memory display
- Timeline visualization
- Partial visualization data APIs

**Deliverables**:
- ✅ RankedMemoryVisualization component
- ✅ TimelineVisualization component
- ✅ Basic visualization data APIs""",
            "status": "Done",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Knowledge Graph Network Component",
            "description": """**Objective**: Implement interactive network \
visualization of memory relationships using D3.js.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] React/TypeScript Component:
  - Create `<KnowledgeGraphNetwork />` component
  - Implement force-directed layout with D3.js
  - Node types: Memories (circles), Contexts (squares), Tags (diamonds)
  - Edge types: References, Discussions, Approvals, AI-suggested
- [ ] Interactive Features:
  - Zoom, pan, drag functionality
  - Node/edge selection and highlighting
  - Hover details and tooltips
  - Detail panel updates on selection
- [ ] Visual Design:
  - Node sizes based on PageRank scores
  - Node colors based on sentiment/type
  - Edge weights based on connection strength
  - Smooth animations and transitions
- [ ] Real-time Updates:
  - WebSocket integration for live updates
  - Smooth animation of new connections
  - Visual state synchronization

**Acceptance Criteria**:
- [ ] Force-directed graph renders correctly
- [ ] All node types display with correct shapes
- [ ] All edge types display with correct styling
- [ ] Interactive features work smoothly
- [ ] Real-time updates animate correctly
- [ ] Performance: < 1s for 1000+ nodes

**Deliverables**:
- KnowledgeGraphNetwork React component
- D3.js force simulation setup
- Interactive controls (zoom, pan, drag)
- Real-time update integration
- Performance optimizations

**Priority**: High - Primary visualization component""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Memory Impact Trail Component",
            "description": """**Objective**: Implement timeline-based \
visualization showing how a memory influences team knowledge over time.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] React/TypeScript Component:
  - Create `<MemoryImpactTrail />` component
  - Implement timeline-based visualization
  - Branching paths for different discussion threads
  - Impact metrics at each stage
- [ ] Interactive Features:
  - Timeline playback with speed controls
  - Interactive exploration of impact events
  - Zoom into specific time periods
  - Drill-down to specific events
- [ ] Visual Design:
  - Animated path drawing
  - Timeline markers for events
  - Impact score visualization
  - Influence radius display
- [ ] Data Processing:
  - Calculate chronological impact events
  - Aggregate impact metrics
  - Generate visualization data

**Acceptance Criteria**:
- [ ] Timeline positions events correctly
- [ ] Animated trail drawing works smoothly
- [ ] Playback controls functional
- [ ] Impact metrics display accurately
- [ ] Branching paths render correctly

**Deliverables**:
- MemoryImpactTrail React component
- Timeline visualization with D3.js
- Animation and playback controls
- Impact event processing
- Interactive exploration

**Priority**: High - Secondary visualization component""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Collaboration Heatmap Component",
            "description": """**Objective**: Implement 2D heatmap showing \
collaboration intensity across knowledge areas.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] React/TypeScript Component:
  - Create `<CollaborationHeatmap />` component
  - Implement 2D heatmap visualization
  - Knowledge topics on axes
  - Intensity color mapping
- [ ] Interactive Features:
  - Time-based animation showing patterns
  - Interactive drill-down to specific activities
  - Team member overlay display
  - Peak detection and highlighting
- [ ] Visual Design:
  - Color interpolation based on activity
  - Temporal pattern visualization
  - Interactive overlay for details
  - Smooth animation transitions
- [ ] Data Processing:
  - Generate collaboration intensity matrix
  - Calculate activity patterns
  - Aggregate team contributions

**Acceptance Criteria**:
- [ ] Heatmap displays correctly with proper colors
- [ ] Time-based animation works smoothly
- [ ] Drill-down functional
- [ ] Team member overlay displays correctly
- [ ] Performance: < 500ms for large datasets

**Deliverables**:
- CollaborationHeatmap React component
- D3.js heatmap visualization
- Time-based animation
- Interactive drill-down
- Team member overlay

**Priority**: Medium - Tertiary visualization component""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: PageRank Visual Feedback Component",
            "description": """**Objective**: Implement radial visualization \
helping users understand why content ranks highly.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] React/TypeScript Component:
  - Create `<PageRankVisualizer />` component
  - Implement radial visualization
  - Memory at center with influence rings
  - Score breakdown visualization
- [ ] Interactive Features:
  - Interactive exploration of ranking factors
  - Comparison mode for multiple memories
  - Detailed breakdown display
  - Factor contribution highlighting
- [ ] Visual Design:
  - Radial layout with rings
  - Direct and indirect connections
  - Visual score components
  - Interactive factor exploration
- [ ] Data Processing:
  - Analyze PageRank factors
  - Break down scores into components
  - Calculate influence contributions

**Acceptance Criteria**:
- [ ] Radial visualization renders correctly
- [ ] Influence rings display accurately
- [ ] Score breakdown shows all factors
- [ ] Comparison mode works
- [ ] Interactive exploration functional

**Deliverables**:
- PageRankVisualizer React component
- Radial visualization with D3.js
- Score breakdown system
- Comparison mode
- Interactive factor exploration

**Priority**: Medium - Quaternary visualization component""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Dedicated Visualization API Endpoints",
            "description": """**Objective**: Create dedicated API endpoints for visualization data.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] API Endpoint: `/visualizations/knowledge-graph`
  - Get graph data for D3.js network visualization
  - Parameters: team_id, depth, min_pagerank
  - Return: nodes, edges with full metadata
- [ ] API Endpoint: `/visualizations/impact-trail/{memory_id}`
  - Get impact trail data for specific memory
  - Return: chronological impact events with metrics
- [ ] API Endpoint: `/visualizations/collaboration-heatmap`
  - Get collaboration intensity data
  - Parameters: team_id, time_range
  - Return: heatmap matrix with activity data
- [ ] API Endpoint: `/visualizations/pagerank-breakdown/{memory_id}`
  - Get detailed PageRank score breakdown
  - Return: factor contributions and analysis
- [ ] Data Processing Functions:
  - Generate optimized layout for D3.js
  - Calculate impact trail events
  - Generate collaboration matrix
  - Analyze PageRank factors

**Acceptance Criteria**:
- [ ] All endpoints return correct data format
- [ ] Performance: < 200ms response time
- [ ] Proper error handling
- [ ] Data format optimized for D3.js
- [ ] Comprehensive test coverage

**Deliverables**:
- Visualization API endpoints
- Data processing functions
- D3.js optimized data format
- API documentation
- Comprehensive tests

**Priority**: High - Required for all visualizations""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: WebSocket Real-time Updates",
            "description": """**Objective**: Implement real-time updates for visualizations via WebSocket.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] WebSocket Server Setup:
  - Create WebSocket endpoint for visualizations
  - `/visualizations/ws/{visualization_type}`
  - Handle multiple client connections
- [ ] Real-time Event Broadcasting:
  - New memory creation events
  - Connection detection events
  - Discussion updates
  - Collaboration activity events
- [ ] Client Integration:
  - WebSocket connection management
  - Event subscription/unsubscription
  - Smooth animation on updates
  - Visual state synchronization
- [ ] Performance Optimization:
  - Efficient event batching
  - Delta updates only
  - Connection pooling
  - Graceful degradation

**Acceptance Criteria**:
- [ ] WebSocket connections establish correctly
- [ ] Events broadcast in real-time (< 100ms latency)
- [ ] Smooth animations on updates
- [ ] Multiple clients supported
- [ ] Graceful error handling

**Deliverables**:
- WebSocket server for visualizations
- Real-time event broadcasting
- Client WebSocket integration
- Performance optimizations
- Connection management

**Priority**: High - Required for live collaboration""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: React/TypeScript Component Integration",
            "description": """**Objective**: Integrate visualization components \
with React/TypeScript frontend and dashboard system.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Component Architecture:
  - Create visualization component library
  - TypeScript interfaces and types
  - Shared visualization utilities
  - Component composition patterns
- [ ] Dashboard Integration:
  - Integration with dashboard widget system
  - Widget configuration for visualizations
  - Dashboard layout support
  - Widget refresh mechanisms
- [ ] State Management:
  - React hooks for visualization data
  - State synchronization
  - Caching and optimization
  - Error boundary implementation
- [ ] Accessibility:
  - Keyboard navigation support
  - Screen reader descriptions
  - ARIA attributes
  - Focus management

**Acceptance Criteria**:
- [ ] Components integrate with dashboard
- [ ] TypeScript types are complete
- [ ] State management works correctly
- [ ] Accessibility score: 95+ on Lighthouse
- [ ] Error handling comprehensive

**Deliverables**:
- React component library
- TypeScript type definitions
- Dashboard integration
- State management hooks
- Accessibility features

**Priority**: High - Required for production use""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Performance Optimization & Testing",
            "description": """**Objective**: Optimize visualization performance and ensure comprehensive testing.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Performance Optimization:
  - Virtualization for large datasets
  - Efficient rendering algorithms
  - Memory usage optimization (< 100MB for large graphs)
  - Rendering performance (< 1s for 1000+ nodes)
- [ ] Testing Suite:
  - Unit tests for all components
  - Integration tests for API endpoints
  - Performance tests for large datasets
  - Accessibility tests
- [ ] Load Testing:
  - Test with 1000+ nodes
  - Test with 5000+ nodes (virtualized)
  - Test real-time update performance
  - Test WebSocket connection limits
- [ ] Documentation:
  - Component usage documentation
  - API documentation
  - Performance guidelines
  - Best practices guide

**Acceptance Criteria**:
- [ ] Performance targets met
- [ ] Test coverage: 90%+
- [ ] Load tests pass
- [ ] Documentation complete

**Deliverables**:
- Performance optimizations
- Comprehensive test suite
- Load test results
- Documentation

**Priority**: High - Required for production quality""",
            "status": "New",
        },
    ]

    # Create stories
    print("\n5️⃣  Creating stories...")
    created_stories = []
    failed_stories = []

    for idx, story_data in enumerate(stories, 1):
        print(f"\n   Creating story {idx}/{len(stories)}: " f"{story_data['subject'][:60]}...")

        status_id = None
        if story_data["status"] == "Done":
            done_status_id = get_status_id(headers, project_id, "Done")
            status_id = done_status_id
        else:
            status_id = new_status_id

        created = create_story(
            headers,
            project_id,
            story_data["subject"],
            story_data["description"],
            assignee_id,
            status_id,
        )

        if created:
            ref = created.get("ref")
            created_stories.append((ref, story_data["subject"]))
            print(f"   ✅ Created US#{ref}")
        else:
            failed_stories.append(story_data["subject"])
            print("   ❌ Failed to create story")

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
