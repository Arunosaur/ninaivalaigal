# Grafana Dashboard Loading Troubleshooting

**Issue**: Dashboards not visible in Grafana UI
**Created**: 2025-11-02

---

## ✅ Quick Fix

### **Option 1: Reload Dashboards from UI** (Easiest)

1. **Login to Grafana**: http://localhost:3001
2. **Navigate**: Configuration (⚙️ icon) → Provisioning → Dashboards
3. **Click**: "Reload" button
4. **Or**: Go to Dashboards → Browse → should see dashboards now

### **Option 2: Restart Grafana Container**

```bash
container stop ninaivalaigal-dev-grafana
container start ninaivalaigal-dev-grafana
# Wait 10-15 seconds for Grafana to start
```

### **Option 3: Manually Reload via API** (requires password)

```bash
# Using your new password
curl -X POST http://localhost:3001/api/admin/provisioning/dashboards/reload \
  -u admin:YOUR_NEW_PASSWORD
```

---

## 📊 Verify Dashboards Are Loaded

### **Check Dashboard Files in Container**:
```bash
container exec ninaivalaigal-dev-grafana ls -la /etc/grafana/provisioning/dashboards/*.json
```

**Expected**: Should see 4 JSON files:
- `api-performance-overview.json`
- `business-metrics.json`
- `service-health.json`
- `slo-compliance.json`

### **Check Grafana Logs**:
```bash
container logs ninaivalaigal-dev-grafana 2>&1 | grep -i dashboard
```

Look for messages like:
- "dashboard provisioning completed"
- "dashboard file loaded"
- Any errors about dashboard loading

---

## 📡 Prometheus Datasource Configuration

### **Current Configuration**:
- **URL**: `http://192.168.66.175:9090` (Prometheus container IP)
- **Type**: Prometheus
- **Location**: `/etc/grafana/provisioning/datasources/prometheus.yml`

### **Verify Datasource in Grafana UI**:

1. **Login**: http://localhost:3001
2. **Navigate**: Configuration (⚙️) → Data Sources
3. **Check**: "Prometheus" datasource exists
4. **Click**: "Prometheus" → Test the connection
5. **If Failed**: Update URL to current Prometheus container IP:
   ```bash
   # Get Prometheus IP
   container inspect ninaivalaigal-dev-prometheus | jq -r '.[0].networks[0].address' | cut -d'/' -f1
   ```

### **Update Datasource URL** (if needed):

The datasource URL uses the Prometheus container IP. If Prometheus container was recreated, the IP may have changed.

**To update**:
1. Get new Prometheus IP:
   ```bash
   PROM_IP=$(container inspect ninaivalaigal-dev-prometheus 2>/dev/null | jq -r '.[0].networks[0].address' 2>/dev/null | cut -d'/' -f1)
   echo "Prometheus IP: $PROM_IP"
   ```

2. Update datasource config:
   ```bash
   # Update the config file
   sed -i.bak "s|url: http://.*:9090|url: http://${PROM_IP}:9090|g" config/grafana/datasources/prometheus.yml

   # Copy into container
   cat config/grafana/datasources/prometheus.yml | container exec -i ninaivalaigal-dev-grafana sh -c \
     'cat > /etc/grafana/provisioning/datasources/prometheus.yml'

   # Restart Grafana or reload datasources
   ```

3. **Or update via Grafana UI**:
   - Configuration → Data Sources → Prometheus
   - Update URL field
   - Click "Save & Test"

---

## 🔍 Common Issues

### **Issue 1: Dashboards Not Showing**
**Symptom**: No dashboards in "Browse" menu

**Solutions**:
- ✅ Dashboards copied into container? Check: `container exec ninaivalaigal-dev-grafana ls /etc/grafana/provisioning/dashboards/*.json`
- ✅ Provisioning config correct? Check: `container exec ninaivalaigal-dev-grafana cat /etc/grafana/provisioning/dashboards/default.yml`
- ✅ Reload dashboards (see Option 1 above)
- ✅ Restart Grafana container

### **Issue 2: Prometheus Datasource Not Working**
**Symptom**: Dashboards show "No data" or datasource test fails

**Solutions**:
- ✅ Check Prometheus is running: `container list | grep prometheus`
- ✅ Verify Prometheus URL in datasource config
- ✅ Test Prometheus directly: `curl http://192.168.66.175:9090/api/v1/status/config`
- ✅ Update datasource URL to current Prometheus container IP
- ✅ Check Grafana can reach Prometheus (same network)

### **Issue 3: Dashboard Panels Show "No Data"**
**Symptom**: Dashboards load but panels show "No data"

**Possible Causes**:
- Prometheus not collecting metrics from services
- Metric names don't match (check Prometheus targets)
- Time range in dashboard is wrong
- Services not generating metrics

**Check**:
1. Prometheus Targets: http://localhost:9090/targets
2. Metrics available: `curl http://localhost:9090/api/v1/label/__name__/values | jq .data[]`
3. Test query in Grafana: Explore → Prometheus → enter metric name

---

## 📋 Step-by-Step Verification

1. **Login to Grafana**: http://localhost:3001 (with your password)
2. **Check Data Sources**:
   - Configuration → Data Sources
   - Should see "Prometheus"
   - Click it → "Test" → Should show "Data source is working"
3. **Check Dashboards**:
   - Dashboards → Browse
   - Should see 4 dashboards
   - If not, try: Configuration → Provisioning → Dashboards → Reload
4. **View a Dashboard**:
   - Click any dashboard
   - Panels may show "No data" if services aren't generating metrics yet
   - That's normal if services are just starting

---

## 🔧 Manual Dashboard Import (If Provisioning Fails)

If provisioning doesn't work, you can import dashboards manually:

1. **In Grafana UI**:
   - Dashboards → Import
   - Upload JSON file: `/config/grafana/dashboards/api-performance-overview.json`
   - Repeat for other 3 dashboards

2. **Or via API** (requires password):
   ```bash
   curl -X POST http://localhost:3001/api/dashboards/db \
     -u admin:YOUR_PASSWORD \
     -H "Content-Type: application/json" \
     -d @config/grafana/dashboards/api-performance-overview.json
   ```

---

**Last Updated**: 2025-11-02
**For US#102**: Grafana Monitoring Dashboards
