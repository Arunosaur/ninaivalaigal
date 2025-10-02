# 9 Combination Validation Plan

## 🎯 Objective
Validate all 9 runtime/environment combinations work correctly before adding participants.

## 📊 The 9 Combinations Matrix

### Development Environment
1. ✅ **docker-dev-up** - Docker dev (ports: 5432, 6379, 13370, 8081)
2. ✅ **colima-dev-up** - Colima dev (ports: 5442, 6389, 13380, 8091)
3. 🔄 **apple-dev-up** - Apple CLI dev (ports: 5452, 6399, 13390, 8101)

### Test Environment
4. ⏳ **docker-test-up** - Docker test (ports: 5532, 6479, 13470)
5. ⏳ **colima-test-up** - Colima test (ports: 5542, 6489, 13480)
6. ⏳ **apple-test-up** - Apple CLI test (ports: 5552, 6499, 13490)

### Production Environment
7. ⏳ **docker-prod-up** - Docker prod (ports: 5632, 6579, 13570)
8. ⏳ **colima-prod-up** - Colima prod (ports: 5642, 6589, 13580)
9. ⏳ **apple-prod-up** - Apple CLI prod (ports: 5652, 6599, 13590)

## ✅ Validation Checklist (Per Combination)

### 1. Stack Health
- [ ] Database container running and healthy
- [ ] Redis container running and healthy
- [ ] API container running and healthy
- [ ] All containers on correct ports

### 2. API Endpoints
- [ ] `/health` returns 200 OK
- [ ] `/health/detailed` shows all services healthy
- [ ] `/docs` OpenAPI documentation accessible

### 3. Authentication Flow
- [ ] User signup works
- [ ] User login returns JWT token
- [ ] Protected endpoints require authentication
- [ ] Admin endpoints require admin role

### 4. Admin Console
- [ ] Login page accessible
- [ ] Admin user can login
- [ ] Analytics dashboard shows real data
- [ ] All API endpoints return data (not 404/500)

### 5. Customer App
- [ ] App loads on correct port
- [ ] Can connect to API
- [ ] Displays data correctly

### 6. Data Sharing
- [ ] Database shared across runtimes (same environment)
- [ ] Data persists after container restart
- [ ] No data corruption or conflicts

## 🚀 Execution Plan

### Phase 1: Fix Current Issues (In Progress)
- [x] Fix Team model mapper (invitations/memberships)
- [x] Implement Redis-backed rate limiting
- [ ] Rebuild API container with latest code
- [ ] Test admin login works
- [ ] Verify analytics data displays

### Phase 2: Validate Apple Dev (Current)
- [ ] Run `make apple-dev-up`
- [ ] Execute validation checklist
- [ ] Document any issues
- [ ] Fix and retest

### Phase 3: Validate Other Combinations
- [ ] Test docker-dev-up
- [ ] Test colima-dev-up
- [ ] Test all 3 test environments
- [ ] Test all 3 prod environments

### Phase 4: Automated Testing
- [ ] Run `scripts/test-all-9-combinations.sh`
- [ ] Verify data sharing works
- [ ] Check all health endpoints
- [ ] Validate port matrix

## 📝 Success Criteria

**Ready for Participants When:**
1. ✅ All 9 combinations pass validation
2. ✅ Admin console works in all environments
3. ✅ Customer app works in all environments
4. ✅ Authentication works consistently
5. ✅ Data sharing validated
6. ✅ No port conflicts
7. ✅ Documentation updated
8. ✅ Quick start guide tested

## 🎯 Current Status

**Apple Dev Environment:**
- Database: ✅ Running (port 5452)
- Redis: ✅ Running (port 6399)
- API: 🔄 Rebuilding with fixes
- Customer App: ✅ Running (port 8101)
- Admin Console: ✅ Running (port 8102)

**Blockers:**
- API container needs rebuild with Team model fix
- Once working, validate remaining 8 combinations

**ETA to Participant-Ready:**
- Fix current issues: 15 minutes
- Validate 9 combinations: 30 minutes
- Total: ~45 minutes to fully validated platform
