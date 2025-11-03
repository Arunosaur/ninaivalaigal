# Prometheus Metrics Collection Fix

**Issue**: Grafana dashboards showing "No data" and appearing/disappearing
**Date**: 2025-11-02
**Status**: ⚠️ Partial Fix - Core API working, other services need metrics endpoints

---

## 🔴 Root Cause

1. **Prometheus Configuration**: Initial config used `host.docker.internal:PORT` which doesn't resolve in Apple Container CLI
2. **Service Metrics Endpoints**: Some services don't expose Prometheus-format metrics:
   - ✅ Core API: Has `/metrics` endpoint (working)
   - ❌ gRPC Gateway: No `/metrics` endpoint (404)
   - ❌ Memory Service: Returns JSON, not Prometheus format
   - ❓ GraphOps: Unknown if it exposes metrics

---

## ✅ Fix Applied

### **Prometheus Configuration Update**

Updated Prometheus to scrape from host IP using host ports:

```yaml
scrape_configs:
  - job_name: 'core-api'
    static_configs:
      - targets: ['<host-ip>:13390']  # Host port, not container port
    metrics_path: '/metrics'
```

**Script**: `scripts/update-prometheus-targets.sh` - Dynamically resolves container IPs and updates config

---

## 📊 Current Status

### **Working**
- ✅ Prometheus is running and scraping
- ✅ Core API metrics endpoint accessible
- ✅ Prometheus config can be updated dynamically

### **Issues**
- ⚠️ `host.docker.internal` doesn't resolve in Apple Container CLI
- ⚠️ Some services don't expose `/metrics` endpoints
- ⚠️ Memory Service returns JSON instead of Prometheus format

---

## 🔧 Remaining Tasks

### **1. Fix Core API Metrics (if needed)**
If Prometheus shows format errors, verify metrics format:
```bash
curl http://localhost:13390/metrics | head -20
```

### **2. Add Metrics to gRPC Gateway**
The gRPC Gateway needs a `/metrics` endpoint that exposes Prometheus metrics.

**Current**: Returns 404 for `/metrics`
**Needed**: Prometheus-format metrics endpoint

### **3. Add Prometheus Metrics to Memory Service**
Memory Service currently returns JSON at `/metrics`. It needs to expose Prometheus-format metrics.

**Current**: `{"active_connections":0,...}` (JSON)
**Needed**: Prometheus text format metrics

### **4. Test GraphOps Metrics**
Check if GraphOps service exposes metrics and add it to Prometheus config if available.

---

## 🎯 Quick Workaround

**For immediate dashboard visibility:**

1. **Generate some metrics** by making API calls:
   ```bash
   curl http://localhost:13390/health
   curl http://localhost:13390/metrics
   ```

2. **Wait 15-30 seconds** for Prometheus to scrape

3. **Refresh Grafana dashboards** - Core API metrics should appear

4. **Check Prometheus targets**:
   ```bash
   curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | "\(.labels.job): \(.health)"'
   ```

---

## 📋 Long-Term Solution

### **Option 1: Use Container IPs (Recommended for Apple Container CLI)**

Update Prometheus config to use actual container IPs:

```yaml
scrape_configs:
  - job_name: 'core-api'
    static_configs:
      - targets: ['<container-ip>:8000']  # Container IP + internal port
    metrics_path: '/metrics'
```

**Pros**: Direct container-to-container communication
**Cons**: IPs change when containers restart (need dynamic updates)

### **Option 2: Use Host IP (Current)**

Use host IP with host-mapped ports:

```yaml
scrape_configs:
  - job_name: 'core-api'
    static_configs:
      - targets: ['<host-ip>:13390']  # Host IP + host port
    metrics_path: '/metrics'
```

**Pros**: Stable, doesn't change
**Cons**: Requires host firewall to allow container→host access

### **Option 3: Service Discovery**

Implement Prometheus service discovery (DNS, Kubernetes, etc.) for automatic target discovery.

---

## 🔍 Debugging Commands

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[]'

# Check if metrics exist
curl "http://localhost:9090/api/v1/query?query=up"

# Test service metrics endpoints
curl http://localhost:13390/metrics | head -20
curl http://localhost:13395/metrics
curl http://localhost:13393/metrics

# Check Prometheus config
container exec ninaivalaigal-dev-prometheus cat /etc/prometheus/prometheus.yml

# Update Prometheus targets dynamically
./scripts/update-prometheus-targets.sh
```

---

## 📖 Related Documentation

- `docs/GRAFANA_DASHBOARD_TROUBLESHOOTING.md` - Grafana dashboard issues
- `config/ports.nv.yaml` - Port allocation matrix
- `scripts/update-prometheus-targets.sh` - Dynamic Prometheus config update script

---

**Last Updated**: 2025-11-02
**For US#102**: Grafana Monitoring Dashboards
