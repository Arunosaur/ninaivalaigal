# Developer A Task #37 - Load Tester Makefile

.PHONY: help build run test clean install quick-test demo profiles

# Default target
help: ## Show this help message
	@echo "🚀 Ninaivalaigal Load Tester - Developer A Task #37"
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

build: ## Build the load tester binary
	@echo "🔨 Building load tester..."
	go mod tidy
	go build -o bin/load-tester -ldflags "-s -w" .
	@echo "✅ Build complete: bin/load-tester"

install: build ## Build and install to $GOPATH/bin
	@echo "📦 Installing load tester..."
	go install .
	@echo "✅ Installed to $(shell go env GOPATH)/bin/load-tester"

run: build ## Build and run with default settings
	@echo "🚀 Starting load tester..."
	./bin/load-tester

test: ## Run unit tests
	@echo "🧪 Running tests..."
	go test -v ./...

clean: ## Clean build artifacts
	@echo "🧹 Cleaning up..."
	rm -rf bin/
	go clean

# Quick testing commands
quick-test: build ## Run quick smoke test on gRPC Gateway
	@echo "🔍 Running quick smoke test..."
	./bin/load-tester http http://localhost:8080/health \
		--concurrency 1 \
		--requests 5 \
		--timeout 5s

gateway-smoke: build ## Smoke test gRPC Gateway
	@echo "💨 Testing gRPC Gateway endpoints..."
	./bin/load-tester scenario smoke

gateway-load: build ## Load test gRPC Gateway
	@echo "⚡ Load testing gRPC Gateway..."
	./bin/load-tester scenario load

gateway-stress: build ## Stress test gRPC Gateway
	@echo "🔥 Stress testing gRPC Gateway..."
	./bin/load-tester scenario stress

# Demo commands
demo: build ## Run demonstration of load testing capabilities
	@echo "🎬 Running load tester demonstration..."
	@echo ""
	@echo "1️⃣  Quick Health Check..."
	./bin/load-tester http http://localhost:8080/health --concurrency 1 --requests 3 --timeout 2s || true
	@echo ""
	@echo "2️⃣  Memory Service Test..."
	./bin/load-tester http http://localhost:8080/api/v1/memory/remember \
		--method POST \
		--header "Content-Type: application/json" \
		--header "Authorization: Bearer demo-token" \
		--body '{"content":"Demo load test","context":"demonstration"}' \
		--concurrency 5 \
		--requests 10 \
		--timeout 5s || true
	@echo ""
	@echo "3️⃣  Graph Query Test..."
	./bin/load-tester http http://localhost:8080/api/v1/graph/query \
		--method POST \
		--header "Content-Type: application/json" \
		--header "Authorization: Bearer demo-token" \
		--body '{"query":"MATCH (n) RETURN count(n)","timeout_ms":3000}' \
		--concurrency 3 \
		--requests 5 \
		--timeout 5s || true

# Profile testing
profiles: build ## Show available test profiles
	@echo "📋 Available Load Test Profiles:"
	@echo ""
	@echo "🔹 smoke      - Quick verification (1 worker, 10 requests)"
	@echo "🔹 load       - Standard load test (50 workers, 1000 requests)"
	@echo "🔹 stress     - High-load stress (200 workers, 10000 requests)"
	@echo "🔹 spike      - Traffic spike (500 workers, 5000 requests)"
	@echo "🔹 endurance  - Long-running test (100 workers, 30 minutes)"
	@echo "🔹 grpc-gateway - Gateway-specific test (100 workers, 10000 requests)"
	@echo ""
	@echo "Usage: ./bin/load-tester scenario [PROFILE_NAME]"

# Development helpers
dev-test: build ## Test against local development servers
	@echo "🛠️  Testing local development environment..."
	@echo "Testing gRPC Gateway health..."
	./bin/load-tester http http://localhost:8080/health --concurrency 1 --requests 1 || echo "❌ gRPC Gateway not running"
	@echo ""
	@echo "Testing Memory Service health..."
	./bin/load-tester http http://localhost:13393/health --concurrency 1 --requests 1 || echo "❌ Memory Service not running"
	@echo ""
	@echo "Testing GraphOps Service health..."
	./bin/load-tester http http://localhost:50051/health --concurrency 1 --requests 1 || echo "❌ GraphOps Service not running"

benchmark: build ## Run comprehensive benchmark suite
	@echo "📊 Running comprehensive benchmark suite..."
	@echo ""
	@echo "🎯 Benchmark 1: Health Endpoint Performance"
	./bin/load-tester http http://localhost:8080/health \
		--concurrency 50 \
		--duration 30s \
		--rate-limit 1000 \
		--keep-alive true \
		--timeout 1s
	@echo ""
	@echo "🎯 Benchmark 2: Memory Operations"
	./bin/load-tester http http://localhost:8080/api/v1/memory/remember \
		--method POST \
		--header "Content-Type: application/json" \
		--header "Authorization: Bearer benchmark-token" \
		--body '{"content":"Benchmark test memory","context":"performance_benchmark"}' \
		--concurrency 25 \
		--duration 60s \
		--rate-limit 500 \
		--ramp-up 10s \
		--ramp-down 10s
	@echo ""
	@echo "🎯 Benchmark 3: Graph Queries"
	./bin/load-tester http http://localhost:8080/api/v1/graph/query \
		--method POST \
		--header "Content-Type: application/json" \
		--header "Authorization: Bearer benchmark-token" \
		--body '{"query":"MATCH (n) RETURN n LIMIT 5","timeout_ms":2000}' \
		--concurrency 20 \
		--duration 45s \
		--rate-limit 200 \
		--ramp-up 15s \
		--ramp-down 15s

# Continuous testing
continuous: build ## Run continuous load testing (30 minutes)
	@echo "♾️  Starting continuous load testing..."
	./bin/load-tester scenario endurance

# Performance validation
validate: build ## Validate service performance against SLAs
	@echo "✅ Validating service performance..."
	@echo "Running SLA validation tests..."
	./bin/load-tester http http://localhost:8080/health \
		--concurrency 100 \
		--duration 60s \
		--rate-limit 2000 \
		--timeout 100ms || echo "⚠️  Health endpoint may not meet SLA"

# Docker support
docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t ninaivalaigal/load-tester:latest .

docker-run: docker-build ## Run in Docker container
	@echo "🐳 Running load tester in Docker..."
	docker run --rm --network host ninaivalaigal/load-tester:latest

# Status and information
status: ## Show current service status
	@echo "📊 Service Status Check:"
	@echo ""
	@curl -s http://localhost:8080/health | jq . 2>/dev/null || echo "❌ gRPC Gateway not responding"
	@echo ""
	@curl -s http://localhost:13393/health 2>/dev/null || echo "❌ Memory Service not responding"
	@echo ""
	@curl -s http://localhost:50051/health 2>/dev/null || echo "❌ GraphOps Service not responding"

version: build ## Show version information
	@./bin/load-tester --version

# Installation verification
verify: build ## Verify installation and basic functionality
	@echo "🔍 Verifying load tester installation..."
	@./bin/load-tester --help > /dev/null && echo "✅ CLI interface working"
	@./bin/load-tester http --help > /dev/null && echo "✅ HTTP testing available"
	@./bin/load-tester scenario --help > /dev/null && echo "✅ Scenario testing available"
	@echo "🎉 Load tester verification complete!"
