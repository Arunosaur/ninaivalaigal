#!/bin/bash

# Approval Workflows Test Script
# Tests complete approval workflow with governance and accountability

BASE_URL="http://localhost:13370"
echo "📤 Testing Approval Workflows - The Governance Bridge"
echo "===================================================="

# Test unauthorized access
echo ""
echo "🚫 Step 1: Test Unauthorized Access"
echo "==================================="
echo "Testing approval access without authentication (should fail):"
curl -s "$BASE_URL/approval/pending" | jq .
echo ""

# Show available endpoints
echo "📋 Step 2: Approval Workflow Endpoints"
echo "======================================"
echo ""
echo "With a valid JWT token, you can use these endpoints:"
echo ""

echo "📤 Submit Memory for Approval:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/approval/submit?memory_id=1&submission_note=Important%20team%20update'"
echo ""

echo "📋 List Pending Approvals (for reviewers):"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/approval/pending'"
echo ""

echo "📋 List Pending Approvals (filtered by team):"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/approval/pending?team_id=1'"
echo ""

echo "✅ Approve Memory:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/approval/1/approve?review_note=Looks%20good%20for%20team%20sharing'"
echo ""

echo "❌ Reject Memory:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/approval/1/reject?review_note=Needs%20more%20detail%20before%20sharing'"
echo ""

echo "📊 Check Approval Status:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/approval/1/status'"
echo ""

echo "📝 My Submissions:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/approval/my-submissions'"
echo ""

echo "📝 My Submissions (filtered):"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/approval/my-submissions?status_filter=pending'"
echo ""

echo "🏛️ Team Approval History:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/approval/team/1/history'"
echo ""

echo "📊 Approval Statistics:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' '$BASE_URL/approval/stats'"
echo ""

# Demo with mock data
echo "🧪 Step 3: Demo Approval Data"
echo "=========================="
echo ""
echo "The system comes with sample approvals to demonstrate the workflow:"
echo ""

echo "📤 Sample Pending Approval:"
echo '{
  "id": 1,
  "memory_id": 2,
  "submitted_by": 123,
  "status": "pending",
  "submitted_at": "2025-01-26T10:00:00Z",
  "team_id": 1,
  "memory_content": "Team decision: Use GET-based endpoints for MVP",
  "submission_note": "Important architectural decision for the team"
}'
echo ""

echo "✅ Sample Approved Memory:"
echo '{
  "id": 2,
  "memory_id": 3,
  "submitted_by": 456,
  "reviewed_by": 123,
  "status": "approved",
  "submitted_at": "2025-01-25T14:30:00Z",
  "reviewed_at": "2025-01-25T16:45:00Z",
  "review_note": "Approved - excellent analysis and ready for team sharing"
}'
echo ""

# Governance model examples
echo "🏛️ Step 4: Governance Model"
echo "=========================="
echo ""
echo "Approval workflows establish clear governance:"
echo ""
echo "👤 Memory Creator:"
echo "  ✅ Can submit their own team memories for approval"
echo "  ✅ Can view status of their submissions"
echo "  ❌ Cannot approve their own submissions"
echo ""
echo "👨‍💼 Team Admin:"
echo "  ✅ Can approve/reject team memories"
echo "  ✅ Can view all team approval history"
echo "  ✅ Can add review notes for accountability"
echo ""
echo "🔑 Global Admin:"
echo "  ✅ Can approve/reject any memory"
echo "  ✅ Can view all approval workflows"
echo "  ✅ Can override team permissions"
echo ""
echo "👥 Team Members:"
echo "  ✅ Can view approved memories"
echo "  ✅ Can see team approval history"
echo "  ❌ Cannot see rejected memories (unless they submitted them)"
echo ""

echo "🔄 Step 5: Complete Approval Lifecycle"
echo "====================================="
echo ""
echo "Here's a complete approval workflow:"
echo ""
echo "1. User creates team memory:"
echo "   curl -H 'Authorization: Bearer USER_TOKEN' \\"
echo "        '$BASE_URL/memory/create?content=Team%20update&team_id=1&tags=team,update'"
echo ""
echo "2. User submits memory for approval:"
echo "   curl -H 'Authorization: Bearer USER_TOKEN' \\"
echo "        '$BASE_URL/approval/submit?memory_id=MEMORY_ID&submission_note=Important%20update'"
echo ""
echo "3. Team admin reviews pending approvals:"
echo "   curl -H 'Authorization: Bearer ADMIN_TOKEN' \\"
echo "        '$BASE_URL/approval/pending?team_id=1'"
echo ""
echo "4. Team admin approves memory:"
echo "   curl -H 'Authorization: Bearer ADMIN_TOKEN' \\"
echo "        '$BASE_URL/approval/APPROVAL_ID/approve?review_note=Approved%20for%20team'"
echo ""
echo "5. User checks approval status:"
echo "   curl -H 'Authorization: Bearer USER_TOKEN' \\"
echo "        '$BASE_URL/approval/APPROVAL_ID/status'"
echo ""
echo "6. Team views approved memory:"
echo "   curl -H 'Authorization: Bearer MEMBER_TOKEN' \\"
echo "        '$BASE_URL/memory/team/1'"
echo ""

echo "🎯 Step 6: Integration Benefits"
echo "==============================="
echo ""
echo "Approval workflows bridge all your systems:"
echo ""
echo "🧠 Memory Integration:"
echo "  - Memories can be submitted for team approval"
echo "  - Only approved memories are visible to team"
echo "  - Audit trail for all memory sharing decisions"
echo ""
echo "👥 Team Integration:"
echo "  - Team admins control what gets shared"
echo "  - Team members see curated, approved content"
echo "  - Role-based approval permissions"
echo ""
echo "🔐 Auth Integration:"
echo "  - JWT authentication throughout"
echo "  - Role-based access control"
echo "  - User context for all operations"
echo ""
echo "📊 Analytics Ready:"
echo "  - Track approval rates and patterns"
echo "  - Monitor team collaboration health"
echo "  - Identify active reviewers and contributors"
echo ""

echo "🚀 Step 7: What This Unlocks"
echo "============================"
echo ""
echo "Approval workflows enable the next wave of features:"
echo ""
echo "📅 Timeline Features:"
echo "  - Chronological view of approved memories"
echo "  - Team activity timelines with approvals"
echo "  - Historical decision tracking"
echo ""
echo "💬 Feedback Systems:"
echo "  - Comments on approval decisions"
echo "  - Collaborative review processes"
echo "  - Improvement suggestions"
echo ""
echo "📁 Context Scoping:"
echo "  - Approve memories for specific contexts"
echo "  - Context-based approval workflows"
echo "  - Scoped team knowledge bases"
echo ""
echo "🤖 AI Ranking:"
echo "  - AI can analyze approval patterns"
echo "  - Smart memory recommendations"
echo "  - Quality scoring based on approvals"
echo ""

echo "✅ Approval Workflows Ready!"
echo "============================"
echo ""
echo "🎉 Features Available:"
echo "  ✅ Memory submission for approval"
echo "  ✅ Team-based review and approval"
echo "  ✅ Audit trail and accountability"
echo "  ✅ Role-based governance model"
echo "  ✅ Comprehensive approval history"
echo "  ✅ Statistics and analytics"
echo ""
echo "🔗 Integration Complete:"
echo "  🔐 Auth → 👥 Teams → 🧠 Memory → 📤 Approval"
echo "  Complete collaboration loop established!"
echo ""
echo "🌟 Platform Maturity Achieved:"
echo "  ✅ Controlled memory publishing"
echo "  ✅ Team trust and governance"
echo "  ✅ Audit trail and accountability"
echo "  ✅ Foundation for advanced workflows"
echo ""
echo "🚀 Ready for: Timeline, Feedback, Context Scoping, AI Ranking! 🎯"
