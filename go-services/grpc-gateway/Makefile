# Developer A Task #36 - gRPC Gateway Makefile

.PHONY: help build run test clean docker proto deps

# Default target
help: ## Show this help message
	@echo "🚀 gRPC Gateway - Developer A Task #36"
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

deps: ## Install Go dependencies
	@echo "📦 Installing dependencies..."
	go mod tidy
	go mod download

build: deps ## Build the gateway binary
	@echo "🔨 Building gRPC Gateway..."
	go build -o bin/grpc-gateway .

run: ## Run the gateway locally
	@echo "🚀 Starting gRPC Gateway on :8080..."
	go run main.go

test: ## Run tests
	@echo "🧪 Running tests..."
	go test -v ./...

clean: ## Clean build artifacts
	@echo "🧹 Cleaning up..."
	rm -rf bin/
	go clean

docker: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t ninaivalaigal/grpc-gateway:latest .

docker-run: docker ## Run in Docker container
	@echo "🐳 Running gRPC Gateway in Docker..."
	docker run --rm -p 8080:8080 --name grpc-gateway ninaivalaigal/grpc-gateway:latest

proto: ## Generate protobuf code
	@echo "📡 Generating protobuf code..."
	cd proto && chmod +x generate.sh && ./generate.sh
	@echo "✅ Protobuf generation complete"

health: ## Check gateway health
	@echo "🏥 Checking gateway health..."
	@curl -s http://localhost:8080/health | jq . || echo "Gateway not running or jq not installed"

benchmark: ## Run simple benchmark
	@echo "⚡ Running simple benchmark..."
	@echo "Testing health endpoint with 100 requests, 10 concurrent..."
	@which ab > /dev/null || (echo "❌ Apache Bench (ab) not installed"; exit 1)
	ab -n 100 -c 10 http://localhost:8080/health

# Development helpers
dev: run ## Alias for run

install: deps build ## Install dependencies and build

# Show current status
status: ## Show current implementation status
	@echo "📊 Developer A Task #36 Status:"
	@echo "✅ Go module initialized"
	@echo "✅ Basic HTTP server"
	@echo "✅ Health endpoint"
	@echo "✅ CORS & logging middleware"
	@echo "✅ Docker configuration"
	@echo "🚧 gRPC integration (next step)"
	@echo "⏳ Protocol buffer definitions"
	@echo "⏳ Service connections"
