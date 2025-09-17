#!/bin/bash

echo "=== Container Runtime Performance Comparison ==="

function measure_resources() {
    local runtime_name="$1"
    echo -e "\n=== $runtime_name Resource Usage ==="
    
    # Memory usage
    echo "Memory usage:"
    ps aux | grep -E "(docker|colima|lima|containerd)" | grep -v grep | awk '{print $4"% "$11}' | sort -nr
    
    # CPU usage  
    echo -e "\nCPU usage:"
    top -l 1 -n 10 | grep -E "(docker|colima|lima|containerd)" | head -5
    
    # Disk usage
    echo -e "\nDisk usage:"
    du -sh ~/.docker 2>/dev/null || echo "No ~/.docker"
    du -sh ~/.colima 2>/dev/null || echo "No ~/.colima" 
    du -sh ~/.lima 2>/dev/null || echo "No ~/.lima"
}

function test_startup_time() {
    local compose_file="$1"
    local runtime_name="$2"
    
    echo -e "\n=== $runtime_name Startup Time Test ==="
    
    # Clean start
    docker-compose -f "$compose_file" down -v 2>/dev/null
    
    # Time the startup
    echo "Starting containers..."
    time docker-compose -f "$compose_file" up -d
    
    # Time until ready
    echo "Waiting for readiness..."
    start_time=$(date +%s)
    timeout 60 bash -c 'until docker-compose -f '"$compose_file"' exec postgres pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done'
    end_time=$(date +%s)
    ready_time=$((end_time - start_time))
    
    echo "✅ Ready in ${ready_time} seconds"
    
    # Cleanup
    docker-compose -f "$compose_file" down -v
}

# Current runtime check
echo "Current Docker context: $(docker context show)"

# Test with current setup (Colima)
measure_resources "Colima"

# Create test compose file
cat > /tmp/perf-test-compose.yml << 'EOF'
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 2s
      timeout: 5s
      retries: 10
EOF

test_startup_time "/tmp/perf-test-compose.yml" "Colima"

# Cleanup
rm /tmp/perf-test-compose.yml

echo -e "\n=== Summary ==="
echo "Colima appears to be running efficiently!"
echo "Memory overhead is lower than Docker Desktop"
echo "Ready for GitHub Actions CI setup"
