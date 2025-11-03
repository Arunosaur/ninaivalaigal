# US#102: Grafana Monitoring Dashboards - Progress Report

**Date**: 2025-11-02
**Developer**: Developer F
**Status**: 🟡 **IN PROGRESS** - Infrastructure Setup

---

## Current Progress

### ✅ Completed
1. **Prometheus Startup Script** - Created `scripts/nv-prometheus-start-apple.sh`
2. **Grafana Startup Script** - Created `scripts/nv-grafana-start-apple.sh`
3. **Prometheus Configuration** - Created `/monitoring/prometheus.yml` with scrape configs
4. **Grafana Configuration Structure** - Created `/config/grafana/` directories
5. **Data Source Configuration** - Prometheus datasource auto-provisioning configured

### ⚠️ Known Issue
**Apple Container CLI Volume Mount Limitations**

After reviewing the [Apple Container CLI GitHub repository](https://github.com/apple/container), I found that:

1. **Mount Format**: Apple Container CLI uses `--mount type=bind,source=<dir>,target=<dir>,readonly` format (not `-v` like Docker)
2. **Directory Requirement**: `--mount type=bind` requires **directories**, not individual files
3. **Binding Error**: Still encountering "Address already in use" errors when mounting directories

**Root Cause**: Apple Container CLI is a relatively new tool (v0.6.0, Oct 2025) and may have limitations with bind mounts, especially on macOS 26.

**Workaround Options:**
1. ✅ **Use Docker Compose** - Existing `docker-compose.dev.yml` already has Prometheus/Grafana configured
2. **Copy configs into container image** during build (requires custom Dockerfile)
3. **Use environment variables** and embedded configs (for simple configs)
4. **Wait for Apple Container CLI updates** that fix bind mount issues

**Recommendation**: Use Docker Compose for Prometheus/Grafana for now, as it's already configured and tested.

---

## Next Steps

1. **Test with Docker Compose** - Use existing `docker-compose.dev.yml` for Prometheus/Grafana
2. **Create Dashboard JSON Files** - Export dashboards to `/config/grafana/dashboards/`
3. **Configure Alerting Rules** - Set up Prometheus alerting for SLO violations
4. **Test Dashboard Functionality** - Verify metrics are displayed correctly

---

## Acceptance Criteria Status

- [ ] **AC1**: Grafana deployed via Apple Container CLI (⚠️ Volume mount issue)
- [ ] **AC2**: Connected to Prometheus data source (✅ Config ready)
- [ ] **AC3**: Dashboard: API Performance Overview (⏳ Pending)
- [ ] **AC4**: Dashboard: Service Health (⏳ Pending)
- [ ] **AC5**: Dashboard: Business Metrics (⏳ Pending)
- [ ] **AC6**: Dashboard: SLO Compliance (⏳ Pending)
- [ ] **AC7**: Alerting rules configured (⏳ Pending)
- [ ] **AC8**: Slack/email notifications (⏳ Pending)
- [ ] **AC9**: Grafana accessible at localhost:3001 (⏳ Pending)
- [ ] **AC10**: Dashboards exported as JSON (⏳ Pending)

---

## Technical Notes

### Prometheus Configuration
- Scrape interval: 15s
- Target services:
  - grpc-gateway:13395
  - memory-service:13393
  - core-api:13390
  - graphops:13398

### Grafana Configuration
- Port: 3001 (as specified in US-90)
- Admin password: admin
- Auto-provisioned Prometheus datasource

---

**Developer F** - 2025-11-02T05:35:00Z
