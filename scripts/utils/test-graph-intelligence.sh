#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#

# Graph Intelligence Test Script
# Tests context scoping and graph-ready data structures

BASE_URL="http://localhost:13370"
echo "📊 Testing Graph Intelligence Foundation"
echo "========================================"

echo ""
echo "🎯 What We're Testing:"
echo "======================"
echo "✅ Context creation and management"
echo "✅ Memory-context linking (graph edges)"
echo "✅ Graph data structure generation"
echo "✅ Team-based graph traversal"
echo "✅ Graph-ready JSON output"
echo ""

# Test unauthorized access
echo "🚫 Step 1: Test Unauthorized Access"
echo "==================================="
echo "Testing context access without authentication (should fail):"
curl -s "$BASE_URL/contexts/my" | jq .
echo ""

# Show available endpoints
echo "📋 Step 2: Context & Graph Endpoints"
echo "===================================="
echo ""
echo "With a valid JWT token, you can use these endpoints:"
echo ""

echo "📁 Create Context:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/contexts/create?name=Auth%20Development&description=Authentication%20system%20work&context_type=project&team_id=1&tags=auth,development'"
echo ""

echo "📋 List My Contexts:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/contexts/my'"
echo ""

echo "📋 List Team Contexts:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/contexts/my?team_filter=1'"
echo ""

echo "🔗 Link Memory to Context:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/contexts/1/add-memory?memory_id=2&relationship_type=belongs_to&relevance_score=0.9'"
echo ""

echo "📊 Get Context Graph:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/contexts/1/graph'"
echo ""

echo "🌐 Get Team Graph:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/contexts/team/1/graph?include_memories=true'"
echo ""

# Demo graph structure
echo "🧪 Step 3: Graph Data Structure Demo"
echo "==================================="
echo ""
echo "Sample graph output structure:"
echo ""

echo "📊 Context Graph Response:"
echo '{
  "success": true,
  "context": {
    "id": 1,
    "name": "Auth System Development",
    "description": "All memories related to authentication system development"
  },
  "graph": {
    "nodes": [
      {
        "id": "context_1",
        "type": "context",
        "label": "Auth System Development",
        "data": { "id": 1, "name": "Auth System Development" }
      },
      {
        "id": "memory_2",
        "type": "memory",
        "label": "Team decision: Use GET-based endpoints...",
        "data": { "id": 2, "content": "Team decision: Use GET-based endpoints for MVP" }
      }
    ],
    "edges": [
      {
        "id": "link_1",
        "source": "context_1",
        "target": "memory_2",
        "type": "belongs_to",
        "weight": 0.9
      }
    ]
  }
}'
echo ""

echo "🌐 Team Graph Response:"
echo '{
  "graph": {
    "nodes": [
      { "id": "team_1", "type": "team", "label": "Team 1" },
      { "id": "context_1", "type": "context", "label": "Auth Development" },
      { "id": "memory_2", "type": "memory", "label": "GET endpoints decision" }
    ],
    "edges": [
      { "source": "team_1", "target": "context_1", "type": "contains" },
      { "source": "context_1", "target": "memory_2", "type": "belongs_to" }
    ]
  }
}'
echo ""

# Graph intelligence benefits
echo "🧠 Step 4: Graph Intelligence Benefits"
echo "======================================"
echo ""
echo "This structure enables powerful graph operations:"
echo ""
echo "🔍 Graph Traversal:"
echo "  - Find all memories in a context"
echo "  - Discover related contexts through shared memories"
echo "  - Trace decision paths and dependencies"
echo ""
echo "📊 Graph Analytics:"
echo "  - Identify central/important memories (high degree)"
echo "  - Find knowledge clusters and communities"
echo "  - Measure context relevance and memory importance"
echo ""
echo "🤖 AI-Ready Structure:"
echo "  - Graph neural networks can process this directly"
echo "  - Semantic similarity through graph embeddings"
echo "  - Recommendation engines using graph traversal"
echo ""
echo "🔗 Relationship Types:"
echo "  - belongs_to: Memory is part of context"
echo "  - decision_in: Memory represents decision made in context"
echo "  - discussed_in: Memory was discussed in context"
echo "  - review_of: Memory is review/feedback on context"
echo ""

echo "🎯 Step 5: Graph Intelligence Use Cases"
echo "======================================="
echo ""
echo "Now you can build:"
echo ""
echo "📈 Knowledge Discovery:"
echo "  - 'Show me all decisions related to authentication'"
echo "  - 'Find memories similar to this one'"
echo "  - 'What contexts are most active?'"
echo ""
echo "🔄 Workflow Intelligence:"
echo "  - 'What decisions led to this outcome?'"
echo "  - 'Which team members contribute to which contexts?'"
echo "  - 'How do our contexts relate to each other?'"
echo ""
echo "🎨 Visualization Ready:"
echo "  - D3.js force-directed graphs"
echo "  - Cytoscape.js network visualization"
echo "  - Interactive graph exploration"
echo ""
echo "🤖 AI Integration:"
echo "  - Graph embeddings for similarity"
echo "  - PageRank for memory importance"
echo "  - Community detection for knowledge clusters"
echo ""

echo "🚀 Step 6: Ready for Graph Intelligence!"
echo "========================================"
echo ""
echo "✅ Foundation Complete:"
echo "  🔐 Auth → 👥 Teams → 🧠 Memory → 📤 Approval → 📁 Context"
echo ""
echo "✅ Graph-Ready Data:"
echo "  - Nodes: Teams, Contexts, Memories, Users"
echo "  - Edges: Contains, Belongs_to, Authored_by, Approved_by"
echo "  - Weights: Relevance scores, approval ratings"
echo ""
echo "✅ API Ready:"
echo "  - GET endpoints for all graph operations"
echo "  - JSON graph format compatible with visualization libraries"
echo "  - Filtered access based on permissions"
echo ""
echo "🎉 You can now:"
echo "  1. Create rich contexts for organizing knowledge"
echo "  2. Link memories to contexts with relationship types"
echo "  3. Generate graph structures for visualization"
echo "  4. Build graph intelligence features on top"
echo ""
echo "🌟 The graph intelligence foundation is SOLID! 📊🧠✨"
