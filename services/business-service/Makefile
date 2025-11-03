# Business Service Makefile (SPEC-100 compliant)
# Follows docs/standards/CONTAINERIZATION_STANDARD.md

.PHONY: help deps build run test clean docker-build docker-export deploy quick-deploy health

SERVICE_NAME := business-service
IMAGE_NAME := ninaivalaigal-$(SERVICE_NAME)
PLATFORM := linux/arm64
TIMESTAMP := $(shell date +%Y%m%d-%H%M%S)
TARBALL := /tmp/$(SERVICE_NAME)-$(TIMESTAMP).tar
ROOT_DIR := $(abspath ../..)

help:
	@echo "Business Service Targets"
	@echo "=========================="
	@echo "make deps           Install Python dependencies"
	@echo "make build          Build the FastAPI app (compile check)"
	@echo "make run            Run locally on port 13391"
	@echo "make test           Run Python tests (if present)"
	@echo "make docker-build   Build arm64 Docker image"
	@echo "make docker-export  Build & export arm64 Docker image to tar"
	@echo "make deploy         Load exported tar into Apple Container CLI"
	@echo "make quick-deploy   Save/load existing image without rebuild"
	@echo "make clean          Remove build artifacts and cached tarballs"
	@echo "make health         Check local /health endpoint"

deps:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

build: deps
	@echo "🔨 Byte-compiling FastAPI modules..."
	python -m compileall main.py routers || true

run:
	@echo "🚀 Starting Business Service on :13391..."
	PORT=13391 python main.py

test:
	@echo "🧪 Running tests (if available)..."
	@if [ -d tests ]; then \
		pytest -v; \
	else \
		echo "(No tests directory found; skipping)"; \
	fi

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf __pycache__/ routers/__pycache__/ lib/__pycache__/
	rm -f /tmp/$(SERVICE_NAME)-*.tar

# Docker build (standard)
docker-build:
	@echo "🐳 Building Docker image for $(PLATFORM)..."
	docker build --platform $(PLATFORM) -t $(IMAGE_NAME):arm64 -f services/business-service/Dockerfile $(ROOT_DIR)
	@echo "✅ Image: $(IMAGE_NAME):arm64"

# Export Docker image to tar (standard)
docker-export: docker-build
	@echo "📦 Exporting Docker image to $(TARBALL)..."
	docker save $(IMAGE_NAME):arm64 -o $(TARBALL)
	@echo "✅ Exported: $(TARBALL)"
	@du -h $(TARBALL)
	@echo "Import with: container image load -i $(TARBALL)"

# Build, export, and load image into Apple Container CLI
deploy: docker-export
	@echo "⏫ Loading tarball into Apple Container CLI..."
	container image load -i $(TARBALL)
	@echo "✅ Image ready. Start with: ./scripts/nv-business-service-start.sh"

quick-deploy: docker-build
	@echo "⚡ Quick deploy (no tarball saved)..."
	docker save $(IMAGE_NAME):arm64 -o /tmp/$(SERVICE_NAME)-latest.tar
	container image load -i /tmp/$(SERVICE_NAME)-latest.tar
	rm /tmp/$(SERVICE_NAME)-latest.tar
	@echo "✅ Image loaded. Start with: ./scripts/nv-business-service-start.sh"

health:
	@echo "🏥 Checking http://localhost:13391/health..."
	curl -s http://localhost:13391/health | jq . || echo "Service not running or jq missing"
