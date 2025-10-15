#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Quick Start Commands for October 15, 2025
# SPEC-100 Stage 1: Refactor Router Boundaries

set -euo pipefail

echo "🌅 Good Morning! Starting SPEC-100 Implementation..."
echo ""

# Navigate to workspace
cd /Users/swami/WorkSpace/ninaivalaigal

# Check git status
echo "📊 Git Status:"
git status --short
echo ""

# Verify infrastructure is running
echo "🔍 Checking infrastructure..."
container list | grep ninaivalaigal | awk '{print "✅", $1}'
echo ""

# SPEC-100 Stage 1: Setup
echo "🚀 SPEC-100 Stage 1: Refactor Router Boundaries"
echo ""

# 1. Create SPEC-100 directory
echo "1️⃣ Creating SPEC-100 directory..."
mkdir -p specs/100-api-container-modularization
touch specs/100-api-container-modularization/router-service-mapping.md
echo "✅ Created specs/100-api-container-modularization/"
echo ""

# 2. Create service stubs
echo "2️⃣ Creating service stub directories..."
mkdir -p services/{core-api,memory-service,graph-ai-service,business-service,admin-vendor-service}
mkdir -p services/core-api/{routers,models,tests}
mkdir -p services/memory-service/{routers,models,tests}
mkdir -p services/graph-ai-service/{routers,models,tests}
mkdir -p services/business-service/{routers,models,tests}
mkdir -p services/admin-vendor-service/{routers,models,tests}
echo "✅ Created service directories"
echo ""

# 3. Create shared contracts directory
echo "3️⃣ Creating shared contracts structure..."
mkdir -p shared/contracts/{auth,memory,graph,business,admin}
touch shared/contracts/__init__.py
touch shared/contracts/auth/__init__.py
touch shared/contracts/memory/__init__.py
touch shared/contracts/graph/__init__.py
touch shared/contracts/business/__init__.py
touch shared/contracts/admin/__init__.py
echo "✅ Created shared contracts structure"
echo ""

# 4. List all routers to map
echo "4️⃣ Analyzing existing routers..."
echo "Server API files:"
ls -1 server/*_api.py 2>/dev/null | wc -l | xargs echo "  API files:"
echo ""
echo "Router files:"
ls -1 server/routers/*.py 2>/dev/null | wc -l | xargs echo "  Router files:"
echo ""

# 5. Create initial mapping template
echo "5️⃣ Creating router-service mapping template..."
cat > specs/100-api-container-modularization/router-service-mapping.md << 'EOF'
# Router-Service Mapping

**Created:** October 15, 2025
**Status:** 🟡 In Progress

## Overview
Map 54 existing routers to 5 new microservices.

---

## Service 1: Core API (Lightweight + Stateless)

**Purpose:** Authentication, Users, Teams, RBAC
**Dependencies:** Redis, PgBouncer
**Target Build Time:** 2-3 minutes

### Routers
- [ ] `server/auth.py` - Authentication core
- [ ] `server/auth_working.py` - Working auth implementation
- [ ] `server/signup_api.py` - User registration
- [ ] `server/routers/users.py` - User management
- [ ] `server/routers/teams.py` - Team management
- [ ] `server/rbac_middleware.py` - RBAC enforcement
- [ ] `server/rbac_models.py` - RBAC models

### Models to Extract
- User, Team, Role, Permission
- RefreshToken, Invitation
- Auth request/response schemas

### Dependencies (requirements.txt)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pyjwt==2.8.0
passlib==1.7.4
python-multipart==0.0.6
redis==5.0.1
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
```

---

## Service 2: Memory Service (Memory Substrate)

**Purpose:** Context, Recording, State Persistence
**Dependencies:** PgBouncer, Redis
**Target Build Time:** 3-4 minutes

### Routers
- [ ] `server/memory_system.py` - Core memory operations
- [ ] `server/memory_*.py` - Memory-related APIs
- [ ] `server/context_*.py` - Context management
- [ ] `server/recording_*.py` - Recording ingestion
- [ ] `server/routers/memory.py` - Memory CRUD
- [ ] `server/routers/contexts.py` - Context operations

### Models to Extract
- Memory, Context, Recording
- MemoryMetadata, ContextScope
- Recording schemas

### Dependencies
```
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
pydantic==2.5.0
```

---

## Service 3: Graph/AI Service (Heavy Compute)

**Purpose:** Graph Intelligence, AI Feedback, ML Processing
**Dependencies:** PgBouncer, Redis
**Target Build Time:** 4-5 minutes

### Routers
- [ ] `server/graph_*.py` - Graph operations
- [ ] `server/insights_api.py` - Insight generation
- [ ] `server/discussion_api.py` - AI discussions
- [ ] `server/ai_*.py` - AI processing
- [ ] `server/routers/graph_*.py` - Graph routes

### Models to Extract
- GraphNode, GraphEdge
- Insight, Discussion
- AI feedback schemas

### Dependencies
```
scikit-learn==1.3.0
numpy==1.24.3
pandas==2.0.3
torch==2.0.1  # if using PyTorch
networkx==3.1  # for graph operations
```

---

## Service 4: Business Service (Scalable)

**Purpose:** Billing, Usage Tracking, Analytics
**Dependencies:** PgBouncer, Redis, Stripe
**Target Build Time:** 3-4 minutes

### Routers
- [ ] `server/billing_*.py` - Billing operations
- [ ] `server/usage_*.py` - Usage tracking
- [ ] `server/invoice_*.py` - Invoice management
- [ ] `server/subscription_*.py` - Subscriptions
- [ ] `server/analytics_*.py` - Analytics

### Models to Extract
- Subscription, Invoice, UsageRecord
- BillingEvent, PaymentMethod
- Analytics schemas

### Dependencies
```
stripe==7.0.0
reportlab==4.0.7  # for PDF generation
pandas==2.0.3
```

---

## Service 5: Admin/Vendor Service (Internal)

**Purpose:** Admin Console, Vendor Portal
**Dependencies:** PgBouncer, Redis
**Target Build Time:** 2-3 minutes

### Routers
- [ ] `server/vendor_*.py` - Vendor operations
- [ ] `server/admin_*.py` - Admin operations
- [ ] `server/early_adopter_api.py` - Early adopter management

### Models to Extract
- VendorProfile, AdminAction
- Internal schemas

### Dependencies
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
```

---

## Shared Dependencies

These go into `shared/contracts/`:

### Utilities
- Database connection management
- Redis client
- JWT utilities
- Logging/telemetry
- Security/secret redaction

### Cross-Service Contracts
- User schema (used by all services)
- Team schema (used by most services)
- Context schema (used by Memory + Graph)
- Event schemas (for message bus)

---

## Next Steps

1. [ ] Review and validate this mapping
2. [ ] Identify circular dependencies
3. [ ] Extract shared models to `shared/contracts/`
4. [ ] Create Dockerfiles for each service
5. [ ] Set up parallel build pipeline

**Target Completion:** October 16, 2025 EOD
EOF

echo "✅ Created router-service mapping template"
echo ""

# 6. Show next steps
echo "📋 Next Steps:"
echo ""
echo "1. Review and fill out: specs/100-api-container-modularization/router-service-mapping.md"
echo "2. Identify all 54 routers and map them"
echo "3. List shared models to extract"
echo "4. Document dependencies per service"
echo ""
echo "⏱️ Estimated Time: 2-3 hours"
echo ""
echo "🎯 Deliverable: Service stubs created ✅"
echo ""
echo "🚀 Ready to start SPEC-100 Stage 1!"
