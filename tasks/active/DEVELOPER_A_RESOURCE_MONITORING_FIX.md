# Developer A: Resource Monitoring Fix - Apple Container CLI

**Date:** October 21, 2025, 3:20 PM
**Issue:** `container inspect` reports PID 0 (expected with Apple Container CLI)

---

## 🔍 **THE PROBLEM**

```bash
container inspect ninaivalaigal-dev-graphops --format '{{.State.Pid}}'
# Output: 0
```

**Why:** Apple Container CLI uses a different process model than Docker. Container processes run in a VM namespace, not directly on the host.

**Result:** `psutil.Process(0)` fails → CSV logs zeros

---

## ✅ **SOLUTION 1: Prometheus Metrics (RECOMMENDED)**

### **Why This Works:**
- Metrics exported from inside container
- No PID mapping needed
- Industry standard
- Rich metrics (CPU, memory, I/O, network)

### **Implementation:**

#### **1a. Add Prometheus Exporter to GraphOps**

**File:** `rust-services/graphops/src/metrics.rs`

```rust
use prometheus::{Encoder, IntCounter, Histogram, Registry};
use std::sync::Arc;

pub struct Metrics {
    pub registry: Registry,
    pub requests_total: IntCounter,
    pub request_duration: Histogram,
    // ... other metrics
}

impl Metrics {
    pub fn new() -> Self {
        let registry = Registry::new();
        // Register metrics
        Self { registry, ... }
    }

    pub fn export(&self) -> Vec<u8> {
        let mut buffer = vec![];
        let encoder = prometheus::TextEncoder::new();
        encoder.encode(&self.registry.gather(), &mut buffer).unwrap();
        buffer
    }
}
```

#### **1b. Add Metrics Endpoint**

```rust
// Add to main.rs
use axum::{routing::get, Router};

async fn metrics_handler(
    State(metrics): State<Arc<Metrics>>,
) -> impl IntoResponse {
    (StatusCode::OK, metrics.export())
}

let app = Router::new()
    .route("/metrics", get(metrics_handler))
    // ... other routes
```

#### **1c. Scrape Metrics**

**Create:** `scripts/scrape-prometheus.py`

```python
#!/usr/bin/env python3
import csv
import time
import requests
from datetime import datetime

def scrape_metrics(url, output_file, interval=10):
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'service', 'metric', 'value'])

        while True:
            timestamp = datetime.utcnow().isoformat() + 'Z'

            try:
                resp = requests.get(f"{url}/metrics", timeout=5)
                for line in resp.text.split('\n'):
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 2:
                            metric_name = parts[0]
                            value = parts[1]
                            writer.writerow([timestamp, 'graphops', metric_name, value])
            except Exception as e:
                print(f"Error: {e}")

            time.sleep(interval)

if __name__ == "__main__":
    scrape_metrics("http://localhost:13398", "benchmarks/results/metrics.csv", 10)
```

**Pros:**
- ✅ Accurate metrics from source
- ✅ No PID mapping needed
- ✅ Production-ready approach
- ✅ Rich metrics available

**Cons:**
- ⏱️ Requires adding Prometheus to GraphOps
- ⏱️ ~1-2 hours implementation

---

## ✅ **SOLUTION 2: Container Exec Monitoring (QUICK)**

### **Why This Works:**
- Run monitoring inside container
- See container's view of resources
- No PID mapping needed

### **Implementation:**

#### **2a. Create In-Container Monitor**

**File:** `scripts/monitor-from-inside.sh`

```bash
#!/usr/bin/env bash
# Run monitoring from inside container

CONTAINER=${1:-"ninaivalaigal-dev-graphops"}
OUTPUT=${2:-"benchmarks/results/resources_inside.csv"}
INTERVAL=${3:-10}

echo "timestamp,container,cpu_percent,mem_mb,mem_percent" > "$OUTPUT"

while true; do
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Run top inside container, parse output
    stats=$(container exec "$CONTAINER" sh -c '
        top -b -n 1 | grep "Cpu(s)" | awk "{print \$2}" | tr -d "%"
        free -m | grep Mem | awk "{print \$3, \$2}"
    ')

    # Parse stats
    read -r cpu mem_used mem_total <<< "$stats"
    mem_percent=$(awk "BEGIN {printf \"%.2f\", ($mem_used/$mem_total)*100}")

    echo "$timestamp,$CONTAINER,$cpu,$mem_used,$mem_percent" >> "$OUTPUT"

    sleep "$INTERVAL"
done
```

**Usage:**

```bash
# Run monitoring
./scripts/monitor-from-inside.sh \
  ninaivalaigal-dev-graphops \
  benchmarks/results/resources.csv \
  10 &
MONITOR_PID=$!

# Your benchmark
python3 scripts/mcp_mix_run.py ...

# Stop
kill $MONITOR_PID
```

**Pros:**
- ✅ Quick to implement (15 minutes)
- ✅ No code changes to GraphOps
- ✅ Works with Apple Container CLI

**Cons:**
- ⚠️ Less accurate than Prometheus
- ⚠️ Requires `top`/`free` in container

---

## ✅ **SOLUTION 3: Host Process Monitoring (WORKAROUND)**

### **Why This Works:**
- Monitor host processes by name
- Works around PID 0 issue

### **Implementation:**

#### **3a. Find Process by Name**

```bash
# Find GraphOps process on host
ps aux | grep graphops | grep -v grep
```

#### **3b. Modified psutil Monitor**

```python
#!/usr/bin/env python3
import csv
import psutil
import time
from datetime import datetime

def find_process_by_name(name):
    """Find process by name substring."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if name in process name or cmdline
            if name.lower() in proc.info['name'].lower():
                return proc.pid
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline']).lower()
                if name.lower() in cmdline:
                    return proc.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

def monitor_by_name(process_name, output_file, interval=10):
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'process', 'pid', 'cpu_percent', 'memory_mb'])

        while True:
            timestamp = datetime.utcnow().isoformat() + 'Z'

            pid = find_process_by_name(process_name)

            if pid:
                try:
                    proc = psutil.Process(pid)
                    cpu = proc.cpu_percent(interval=0.1)
                    mem = proc.memory_info().rss / (1024 * 1024)

                    writer.writerow([timestamp, process_name, pid, cpu, mem])
                    print(f"{timestamp} | {process_name} | CPU: {cpu:.2f}% | Mem: {mem:.2f}MB")
                except psutil.NoSuchProcess:
                    writer.writerow([timestamp, process_name, 0, 0.0, 0.0])
            else:
                writer.writerow([timestamp, process_name, 0, 0.0, 0.0])
                print(f"{timestamp} | {process_name} | Not found")

            time.sleep(interval)

if __name__ == "__main__":
    monitor_by_name("graphops", "benchmarks/results/resources.csv", 10)
```

**Pros:**
- ✅ Works around PID 0 issue
- ✅ No container changes needed

**Cons:**
- ⚠️ Process name matching fragile
- ⚠️ May miss container processes

---

## 🎯 **RECOMMENDATION**

### **For Immediate Benchmarking:**

**Use Solution 3 (Host Process Monitoring)** - Quick workaround

```bash
# Modified psutil script to find by name
python3 scripts/monitor-by-name.py graphops benchmarks/results/resources.csv 10 &
MONITOR_PID=$!

# Run benchmark
python3 scripts/mcp_mix_run.py ...

# Stop
kill $MONITOR_PID
```

---

### **For Production/Final Report:**

**Use Solution 1 (Prometheus)** - Proper metrics

**Implementation Steps:**
1. Add `prometheus` crate to GraphOps
2. Export metrics on `/metrics` endpoint
3. Scrape with Python script
4. Include in cost model analysis

**Time:** 1-2 hours
**Benefit:** Production-ready, accurate metrics

---

## 📊 **What to Report**

### **With Any Solution:**

```
GraphOps CPU: [FILL]% (average during test)
GraphOps Memory: [FILL] MB (average)
Postgres CPU: [FILL]%
Redis CPU: [FILL]%
```

### **Monitoring Method Used:**
```
Method: [Solution 1/2/3]
Data Quality: [Good/Fair/Limited]
```

---

## 🚀 **IMMEDIATE ACTION**

### **Option A: Skip Monitoring for Now**

Focus on latency fix first:
- Create indexes (priority #1)
- Rerun benchmark
- Get latency to <5ms
- Add monitoring later

**Pros:** Focus on critical issue (latency)

---

### **Option B: Quick Host Monitoring**

Use process name matching:

```python
# I'll create monitor-by-name.py if you want this
```

**Pros:** Some resource data for baseline
**Cons:** Not highly accurate

---

### **Option C: Proper Prometheus**

Add metrics to GraphOps:

```rust
// I can provide full implementation if needed
```

**Pros:** Production-ready
**Cons:** 1-2 hour time investment

---

## 💡 **MY RECOMMENDATION**

**Priority Order:**

1. **FIX LATENCY FIRST** (Solution 1 in latency doc)
   - Create AGE indexes
   - Rerun benchmark
   - Get to <5ms P95

2. **THEN ADD MONITORING** (Solution 3 here)
   - Quick process name matching
   - Good enough for baseline report

3. **LATER: PROPER METRICS** (Solution 1 here)
   - Add Prometheus for production
   - Use in final cost model

---

## 📝 **Files to Create**

If you want Solution 3 (quick):
- `scripts/monitor-by-name.py` (I can create this)

If you want Solution 1 (proper):
- Update GraphOps with Prometheus
- Create scraper script
- (1-2 hours work)

---

**FOCUS ON LATENCY FIX FIRST, MONITORING SECOND!** 🎯

The 8-10x latency gap is more critical than resource metrics right now.
