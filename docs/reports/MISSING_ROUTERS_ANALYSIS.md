# Missing Routers - Complete Analysis

**Date:** October 19, 2025, 1:12 AM
**Total in server/:** 42 routers
**Total deployed:** 34 routers (across 4 services)
**Missing:** 8 routers

---

## ❌ **Missing Routers (8 total)**

### 1. `demo_api.py`
**Purpose:** Demo mode features
**Why not deployed:** Low priority, demo functionality
**Recommended location:** Business Service or separate Demo Service
**Impact:** Demo features unavailable

### 2. `enhanced_signup_api.py`
**Purpose:** Enhanced signup flow (probably newer version)
**Status:** We deployed `signup_api.py` to Core API
**Why not deployed:** Likely duplicate/alternative to signup_api.py
**Recommended:** Review if enhanced features needed

### 3. `standalone_teams_api.py`
**Purpose:** Standalone teams operations
**Status:** We have `teams` router in Core API
**Why not deployed:** Likely duplicate of teams.py
**Recommended:** Compare with teams.py, may be legacy

### 4. `standalone_teams_billing_api.py`
**Purpose:** Standalone teams billing
**Status:** We have `team_billing_portal_api.py` in Business Service
**Why not deployed:** Likely duplicate
**Recommended:** Compare with team_billing_portal_api.py

### 5. `suggestions_api.py`
**Purpose:** General suggestions (not memory-specific)
**Status:** We have `memory_suggestions_api.py` in Core API
**Why not deployed:** Uncertain if different from memory_suggestions
**Recommended location:** Core API
**Impact:** General AI suggestions unavailable

### 6. `team_api_keys_api.py`
**Purpose:** Team-level API key management
**Status:** Missing
**Why not deployed:** Overlooked
**Recommended location:** Core API
**Impact:** Team API keys cannot be managed
**Priority:** HIGH - this is important functionality

### 7. `team_invitations_api.py`
**Purpose:** Team invitation system
**Status:** Missing
**Why not deployed:** Overlooked
**Recommended location:** Core API
**Impact:** Cannot invite users to teams
**Priority:** HIGH - this is important functionality

### 8. `unified_macro_intelligence_api.py`
**Purpose:** Macro intelligence and automation
**Status:** Missing
**Why not deployed:** Complex AI features
**Recommended location:** Graph Service
**Impact:** Macro automation unavailable
**Priority:** MEDIUM

---

## ✅ **Routers Successfully Deployed (34 total)**

### Core API (12 routers):
1. ✅ signup_api.py
2. ✅ token_api.py
3. ✅ rbac_api.py
4. ✅ memory_api.py
5. ✅ memory_acl_api.py
6. ✅ memory_drift_api.py
7. ✅ memory_health_api.py
8. ✅ memory_injection_api.py
9. ✅ memory_suggestions_api.py
10. ✅ session_api.py
11. ✅ queue_api.py
12. ✅ preload_api.py

### Business Service (12 routers):
1. ✅ billing_console_api.py
2. ✅ invoice_management_api.py
3. ✅ usage_analytics_api.py
4. ✅ admin_analytics_api.py
5. ✅ billing_engine_integration_api.py
6. ✅ team_billing_portal_api.py
7. ✅ early_adopter_api.py
8. ✅ gamification_api.py
9. ✅ feedback_api.py
10. ✅ partner_ecosystem_api.py
11. ✅ discussion_api.py
12. ✅ timeline_api.py

### Admin/Vendor (3 routers):
1. ✅ vendor_admin_api.py
2. ✅ staff_management_api.py
3. ✅ staff_auth_api.py

### Graph Service (7 routers - 3 enabled, 4 copied but disabled):
**Enabled:**
1. ✅ dashboard_widgets_api.py
2. ✅ ai_feedback_api.py
3. ✅ (graphops_integration.py - not from *_api.py files)

**Copied but disabled (import issues):**
4. ⚠️ graph_intelligence_api.py (disabled)
5. ⚠️ graph_intelligence_integration_api.py (disabled)
6. ⚠️ insights_api.py (disabled)
7. ⚠️ performance_api.py (disabled)
8. ⚠️ agentic_api.py (copied but not in list above - needs verification)

---

## 🔍 **Potential Duplicates to Verify**

### Need to check if these are duplicates:
1. **signup_api.py vs enhanced_signup_api.py** - Are they different?
2. **teams.py vs standalone_teams_api.py** - Which is newer?
3. **team_billing_portal_api.py vs standalone_teams_billing_api.py** - Same functionality?
4. **memory_suggestions_api.py vs suggestions_api.py** - Different scopes?

---

## 🎯 **Recommendations**

### HIGH PRIORITY - Add immediately:
1. ✅ **team_api_keys_api.py** → Core API
2. ✅ **team_invitations_api.py** → Core API

### MEDIUM PRIORITY - Review and add if needed:
3. ⚠️ **suggestions_api.py** → Core API (if different from memory_suggestions)
4. ⚠️ **unified_macro_intelligence_api.py** → Graph Service

### LOW PRIORITY - Verify if needed:
5. ❌ **demo_api.py** → Business Service (demo features)
6. ❌ **enhanced_signup_api.py** → Compare with signup_api.py
7. ❌ **standalone_teams_api.py** → Compare with teams.py
8. ❌ **standalone_teams_billing_api.py** → Compare with team_billing_portal_api.py

---

## 📊 **Updated Endpoint Projection**

### Current:
- Core API: 114 endpoints
- Business Service: 88 endpoints
- Admin/Vendor: 18 endpoints
- Graph Service: 15 endpoints
- **Total: 235 endpoints**

### If we add HIGH PRIORITY routers:
- Core API: +20 endpoints (team_api_keys + team_invitations)
- **Total: 255 endpoints**

### If we add MEDIUM PRIORITY:
- Core API: +10 endpoints (suggestions)
- Graph Service: +15 endpoints (unified_macro_intelligence)
- **Total: 280 endpoints**

### If we enable Graph Service disabled routers:
- Graph Service: +50 endpoints (graph_intelligence, insights, performance, agentic)
- **Total: 330 endpoints**

---

## ✅ **Action Plan**

1. **Immediate (next 30 minutes):**
   - Add team_api_keys_api.py to Core API
   - Add team_invitations_api.py to Core API
   - Rebuild and redeploy Core API
   - Target: 255 endpoints

2. **Short term (next session):**
   - Review suggestions_api.py vs memory_suggestions_api.py
   - Add unified_macro_intelligence_api.py to Graph Service
   - Fix Graph Service lib/ imports
   - Enable disabled Graph routers
   - Target: 280-330 endpoints

3. **Later:**
   - Review potential duplicates
   - Decide on demo_api.py
   - Cleanup any legacy routers

---

**Conclusion:** We're missing 2 HIGH PRIORITY routers (team_api_keys, team_invitations) that should be added immediately. The other 6 are either low priority, potential duplicates, or need verification.
