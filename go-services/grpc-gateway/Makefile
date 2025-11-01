# Makefile for gRPC Gateway
# Follows: docs/standards/CONTAINERIZATION_STANDARD.md

.PHONY: help build run test clean docker-build docker-export deploy proto deps

# Configuration
SERVICE_NAME := grpc-gateway
IMAGE_NAME := ninaivalaigal-grpc-gateway
PLATFORM := linux/arm64
TIMESTAMP := $(shell date +%Y%m%d-%H%M%S)
TARBALL := /tmp/$(SERVICE_NAME)-$(TIMESTAMP).tar

# Default target
help: ## Show this help message
	@echo "gRPC Gateway - Build Targets"
	@echo "============================="
	@echo ""
	@echo "Development:"
	@echo "  make build          - Build Go binary locally"
	@echo "  make run            - Run gateway locally (port 13395)"
	@echo "  make test           - Run test suite"
	@echo "  make proto          - Generate protobuf code"
	@echo "  make clean          - Clean build artifacts"
	@echo ""
	@echo "Docker/Container:"
	@echo "  make docker-build   - Build Docker image for ARM64"
	@echo "  make docker-export  - Export Docker image to tar"
	@echo "  make deploy         - Build, export, and load into Apple Container CLI"
	@echo ""
	@echo "Deployment:"
	@echo "  After 'make deploy', run:"
	@echo "    cd ../../scripts && ./nv-grpc-gateway-start.sh"
	@echo ""

deps: ## Install Go dependencies
	@echo "📦 Installing dependencies..."
	go mod tidy
	go mod download

build: deps ## Build the gateway binary
	@echo "🔨 Building gRPC Gateway..."
	go build -o bin/grpc-gateway .

run: ## Run the gateway locally (port 13395)
	@echo "🚀 Starting gRPC Gateway on :13395..."
	go run .

test: ## Run tests
	@echo "🧪 Running tests..."
	go test -v ./...

clean: ## Clean build artifacts
	@echo "🧹 Cleaning up..."
	rm -rf bin/
	rm -f /tmp/$(SERVICE_NAME)-*.tar
	go clean

# Docker build (standard)
docker-build: ## Build Docker image for ARM64
	@echo "Building Docker image for $(PLATFORM)..."
	docker build --platform $(PLATFORM) -t $(IMAGE_NAME):arm64 .
	@echo "✅ Image: $(IMAGE_NAME):arm64"

# Export Docker image to tar (standard)
docker-export: docker-build ## Export Docker image to tar
	@echo "Exporting Docker image to tarball..."
	docker save $(IMAGE_NAME):arm64 -o $(TARBALL)
	@echo "✅ Exported: $(TARBALL)"
	@du -h $(TARBALL)
	@echo ""
	@echo "Import with:"
	@echo "  container image load -i $(TARBALL)"

# Build, export, and load into Apple Container CLI (standard)
deploy: docker-export ## Build, export, and load into Apple Container CLI
	@echo "Loading image into Apple Container CLI..."
	container image load -i $(TARBALL)
	@echo "✅ Image loaded!"
	@echo ""
	@echo "Verify with:"
	@echo "  container image list | grep $(SERVICE_NAME)"
	@echo ""
	@echo "Start service with:"
	@echo "  cd ../../scripts && ./nv-grpc-gateway-start.sh"

# Generate protobuf code
proto: ## Generate protobuf code
	@echo "📡 Generating protobuf code..."
	cd proto && chmod +x generate.sh && ./generate.sh
	@echo "✅ Protobuf generation complete"

# Quick rebuild (for development iterations)
quick-deploy: docker-build ## Quick deploy (skip export)
	@echo "Quick deploy (skip export)..."
	docker save $(IMAGE_NAME):arm64 -o /tmp/$(SERVICE_NAME)-latest.tar
	container image load -i /tmp/$(SERVICE_NAME)-latest.tar
	rm /tmp/$(SERVICE_NAME)-latest.tar
	@echo "✅ Ready to start!"

# Health check (standard port)
health: ## Check gateway health (port 13395)
	@echo "🏥 Checking gateway health..."
	@curl -s http://localhost:13395/health | jq . || echo "Gateway not running or jq not installed"
